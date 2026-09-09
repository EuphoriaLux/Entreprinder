"""Tests for the coach-facing unverified-profiles page and panel verification.

Covers ``crush_lu.views_coach.coach_unverified_profiles`` and
``crush_lu.views_coach.coach_verify_member``.

The regression these exist to pin: every other coach queue is built on
``ProfileSubmission``, and since the verification pivot
(`views_profile.submit_profile`) a new submitter gets no submission row at
all — so the people most in need of verification were invisible to coaches.
The page must therefore find them from ``CrushProfile.verification_status``
alone, and the verify action must work with no submission and no event
registration in play.
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

CRUSH_LU_URL_SETTINGS = {"ROOT_URLCONF": "azureproject.urls_crush"}


class SiteTestMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Site.objects.get_or_create(
            id=1, defaults={"domain": "testserver", "name": "Test Server"}
        )


class CoachUnverifiedBase(SiteTestMixin, TestCase):
    def setUp(self):
        from crush_lu.models import CrushCoach, CrushProfile, MeetupEvent
        from crush_lu.models.profiles import UserDataConsent

        # Test users share a rate-limit counter through recycled PKs on
        # SQLite; without this a 429 surfaces as an unrelated DoesNotExist.
        cache.clear()

        self.CrushProfile = CrushProfile
        self.UserDataConsent = UserDataConsent
        self.client = Client()

        self.coach_user = self._user("coach@example.com", first_name="Cam")
        self.coach = CrushCoach.objects.create(
            user=self.coach_user, is_active=True, max_active_reviews=10
        )
        self.other_coach_user = self._user("coach2@example.com", first_name="Dana")
        self.other_coach = CrushCoach.objects.create(
            user=self.other_coach_user, is_active=True, max_active_reviews=10
        )

        self.event = MeetupEvent.objects.create(
            title="Verify Night",
            description="event",
            event_type="speed_dating",
            date_time=timezone.now() + timedelta(days=2),
            location="Luxembourg",
            address="1 Test St",
            max_participants=20,
            min_age=18,
            max_age=99,
            registration_deadline=timezone.now() + timedelta(days=1),
            registration_fee=0,
            is_published=True,
        )

    def _user(self, email, **extra):
        user = User.objects.create_user(
            username=email, email=email, password="pass12345", **extra
        )
        from crush_lu.models.profiles import UserDataConsent

        UserDataConsent.objects.filter(user=user).update(crushlu_consent_given=True)
        return user

    def _profile(self, email, *, status="pending", photo=True, name=None, **extra):
        # `display_name` is a property over the User, not a column, so the
        # name a coach sees is set on `first_name` — which is also what the
        # page's search and name-sort key off.
        user = self._user(email, first_name=name or email.split("@")[0])
        return self.CrushProfile.objects.create(
            user=user,
            show_full_name=False,
            gender="M",
            location="Luxembourg",
            verification_status=status,
            # A plain storage key is enough: nothing here opens the file, and
            # both `bool(photo_1)` and the `photo_1=""` filter read the name.
            photo_1="users/1/photos/a.jpg" if photo else "",
            **extra,
        )

    def _list_url(self):
        # Resolved per call, not at import: every crush_lu route lives inside
        # `i18n_patterns`, so the real path carries a language prefix and only
        # resolves once `override_settings` has swapped the URLconf in.
        return reverse("crush_lu:coach_unverified_profiles")

    def _names(self, response):
        return {p.display_name for p in response.context["profiles"]}


@override_settings(**CRUSH_LU_URL_SETTINGS)
class CoachUnverifiedProfilesListTests(CoachUnverifiedBase):
    def test_lists_pending_profile_with_no_submission(self):
        """The core gap: post-pivot submitters have no ProfileSubmission."""
        from crush_lu.models import ProfileSubmission

        self._profile("nosub@example.com", name="NoSub")
        self.assertFalse(ProfileSubmission.objects.exists())

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        self.assertEqual(resp.status_code, 200)
        self.assertIn("NoSub", self._names(resp))

    def test_lists_profile_whose_latest_submission_expired(self):
        """`expire_stale_submissions` left this cohort pending and orphaned."""
        from crush_lu.models import ProfileSubmission

        profile = self._profile("expired@example.com", name="Expired")
        ProfileSubmission.objects.create(profile=profile, status="expired")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        self.assertIn("Expired", self._names(resp))

    def test_lists_rejected_and_incomplete(self):
        self._profile("rej@example.com", status="rejected", name="Rej")
        self._profile("inc@example.com", status="incomplete", name="Inc")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        self.assertEqual(self._names(resp), {"Rej", "Inc"})

    def test_excludes_verified_and_inactive_and_banned(self):
        self._profile("ok@example.com", status="verified", name="Verified")
        self._profile("gone@example.com", name="Inactive", is_active=False)
        banned = self._profile("ban@example.com", name="Banned")
        self.UserDataConsent.objects.filter(user=banned.user).update(
            crushlu_banned=True
        )
        self._profile("here@example.com", name="Waiting")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        self.assertEqual(self._names(resp), {"Waiting"})

    def test_search_matches_display_name_and_email(self):
        self._profile("findme@example.com", name="Zoe")
        self._profile("other@example.com", name="Quentin")

        self.client.force_login(self.coach_user)

        by_name = self.client.get(self._list_url(), {"q": "zo"})
        self.assertEqual(self._names(by_name), {"Zoe"})

        by_email = self.client.get(self._list_url(), {"q": "findme@"})
        self.assertEqual(self._names(by_email), {"Zoe"})

    def test_status_filter_and_chip_counts(self):
        self._profile("p@example.com", name="Pend")
        self._profile("r@example.com", status="rejected", name="Rej")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"status": "rejected"})

        self.assertEqual(self._names(resp), {"Rej"})
        counts = {c["value"]: c["count"] for c in resp.context["status_chips"]}
        # Chip counts describe the searched set BEFORE the status narrowing,
        # so the unselected chips stay clickable with a meaningful number.
        self.assertEqual(counts["all"], 2)
        self.assertEqual(counts["pending"], 1)
        self.assertEqual(counts["rejected"], 1)

    def test_chip_counts_are_not_fragmented_by_the_signal_annotations(self):
        """One row per status, not per (status, signal-combination).

        The queryset carries six `Exists` annotations by the time the counts
        are taken. If any of them reached the GROUP BY, two same-status
        profiles with different signals would come back as two rows and the
        dict comprehension would keep only the last — silently undercounting
        the chip.
        """
        from crush_lu.models import EventRegistration

        attended = self._profile("a@example.com", name="A")
        EventRegistration.objects.create(
            event=self.event, user=attended.user, status="attended"
        )
        self._profile("b@example.com", name="B")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        counts = {c["value"]: c["count"] for c in resp.context["status_chips"]}
        self.assertEqual(counts["pending"], 2)
        self.assertEqual(counts["all"], 2)

    def test_unknown_filter_values_fall_back_to_defaults(self):
        self._profile("p@example.com", name="Pend")

        self.client.force_login(self.coach_user)
        resp = self.client.get(
            self._list_url(),
            {"status": "verified", "signal": "bogus", "sort": "bogus"},
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["status_filter"], "all")
        self.assertEqual(resp.context["signal_filter"], "")
        self.assertEqual(resp.context["sort_mode"], "recent")
        # "verified" must never leak through as a status filter — the page
        # would then render verified members as work waiting to be done.
        self.assertEqual(self._names(resp), {"Pend"})

    def test_attended_signal_finds_the_actual_leak(self):
        """Somebody stood at a door and left unverified."""
        from crush_lu.models import EventRegistration

        attended = self._profile("came@example.com", name="Came")
        EventRegistration.objects.create(
            event=self.event, user=attended.user, status="attended"
        )
        self._profile("never@example.com", name="Never")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "attended"})

        self.assertEqual(self._names(resp), {"Came"})
        row = resp.context["profiles"][0]
        self.assertEqual(row.attended_count, 1)

    def test_no_photo_signal_matches_the_door_auto_verify_skip(self):
        self._profile("nophoto@example.com", name="NoPhoto", photo=False)
        self._profile("haspic@example.com", name="HasPic")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "no_photo"})

        self.assertEqual(self._names(resp), {"NoPhoto"})

    def test_unowned_signal_excludes_profiles_with_an_open_submission(self):
        from crush_lu.models import ProfileSubmission

        owned = self._profile("owned@example.com", name="Owned")
        ProfileSubmission.objects.create(
            profile=owned, status="pending", coach=self.other_coach
        )
        self._profile("orphan@example.com", name="Orphan")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "unowned"})

        self.assertEqual(self._names(resp), {"Orphan"})

    def test_upcoming_events_are_attached_to_the_row(self):
        from crush_lu.models import EventRegistration

        booked = self._profile("booked@example.com", name="Booked")
        EventRegistration.objects.create(
            event=self.event, user=booked.user, status="confirmed"
        )

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "upcoming"})

        self.assertEqual(self._names(resp), {"Booked"})
        self.assertEqual(
            [r.event_id for r in resp.context["profiles"][0].upcoming_events],
            [self.event.id],
        )

    def test_page_renders_in_german(self):
        """A non-English render exercises the blocktrans blocks and the .mo.

        The EN tests never touch the catalogue, so a malformed plural form or
        a msgid that drifted from its template would pass them all and 500 for
        every DE and FR coach.
        """
        self._profile("de@example.com", name="Deutsch")

        self.client.force_login(self.coach_user)
        resp = self.client.get("/de/coach/unverified/")

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Unverifizierte Profile")
        self.assertContains(resp, "1 Profil wartet")

    def test_excludes_profiles_without_crushlu_consent(self):
        """`create_crush_profile_on_login` makes a profile before consent.

        Somebody who abandoned the consent screen never agreed to the Crush.lu
        profile layer, so their name and email must not appear on a team-wide
        coach page.
        """
        no_consent = self._profile("nocons@example.com", name="NoConsent")
        self.UserDataConsent.objects.filter(user=no_consent.user).update(
            crushlu_consent_given=False
        )
        self._profile("consented@example.com", name="Consented")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url())

        self.assertEqual(self._names(resp), {"Consented"})

    def test_upcoming_signal_excludes_an_event_that_already_ended(self):
        """The filter and the rendered badge must agree.

        `live_lookback_cutoff` is a 7-day pre-filter, so an event that started
        two hours ago and ran for one still falls inside it. Matching on it
        alone put the member under "Booked on an event" while the row rendered
        no event badge, because the badge applies the precise end-time check.
        """
        from crush_lu.models import EventRegistration, MeetupEvent

        ended = MeetupEvent.objects.create(
            title="Already Over",
            description="event",
            event_type="speed_dating",
            date_time=timezone.now() - timedelta(hours=2),
            duration_minutes=60,
            location="Luxembourg",
            address="1 Test St",
            max_participants=20,
            min_age=18,
            max_age=99,
            registration_deadline=timezone.now() - timedelta(hours=3),
            registration_fee=0,
            is_published=True,
        )
        past = self._profile("past@example.com", name="Past")
        EventRegistration.objects.create(
            event=ended, user=past.user, status="confirmed"
        )
        booked = self._profile("booked@example.com", name="Booked")
        EventRegistration.objects.create(
            event=self.event, user=booked.user, status="confirmed"
        )

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "upcoming"})

        self.assertEqual(self._names(resp), {"Booked"})

    def test_upcoming_signal_ignores_applied_and_no_show_registrations(self):
        """The badge links to the door scanner, so it must mean a door row.

        `coach_event_checkin` renders `SEAT_HOLDING_STATUSES` plus the
        waitlist. An "applied" curated registration is an expression of
        interest and explicitly not a seat, so accepting everything but
        "cancelled" sent the coach to a scanner where the member has no row.
        """
        from crush_lu.models import EventRegistration

        applicant = self._profile("applied@example.com", name="Applicant")
        EventRegistration.objects.create(
            event=self.event, user=applicant.user, status="applied"
        )
        booked = self._profile("seat@example.com", name="Seated")
        EventRegistration.objects.create(
            event=self.event, user=booked.user, status="confirmed"
        )
        waitlisted = self._profile("wait@example.com", name="Waiting")
        EventRegistration.objects.create(
            event=self.event, user=waitlisted.user, status="waitlist"
        )

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "upcoming"})

        self.assertEqual(self._names(resp), {"Seated", "Waiting"})

    def test_unclaimed_submission_still_counts_as_unowned(self):
        """`coach=NULL` is the Verification Channel's unclaimed state.

        Those are precisely the profiles "No coach owns it" exists to surface,
        so keying the signal on an open row alone made the filter exclude the
        cases it is named after.
        """
        from crush_lu.models import ProfileSubmission

        unclaimed = self._profile("unclaimed@example.com", name="Unclaimed")
        ProfileSubmission.objects.create(
            profile=unclaimed, status="pending", coach=None
        )
        claimed = self._profile("claimed@example.com", name="Claimed")
        ProfileSubmission.objects.create(
            profile=claimed, status="pending", coach=self.other_coach
        )
        self._profile("nosub@example.com", name="NoSub")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "unowned"})

        self.assertEqual(self._names(resp), {"Unclaimed", "NoSub"})

    def test_upcoming_signal_excludes_cancelled_events(self):
        """Cancelling an event leaves its registrations alone.

        Filtering on start time only sent coaches to a door that is not
        happening.
        """
        from crush_lu.models import EventRegistration, MeetupEvent

        cancelled = MeetupEvent.objects.create(
            title="Called Off",
            description="event",
            event_type="speed_dating",
            date_time=timezone.now() + timedelta(days=3),
            location="Luxembourg",
            address="1 Test St",
            max_participants=20,
            min_age=18,
            max_age=99,
            registration_deadline=timezone.now() + timedelta(days=2),
            registration_fee=0,
            is_published=True,
            is_cancelled=True,
        )
        stranded = self._profile("called@example.com", name="Stranded")
        EventRegistration.objects.create(
            event=cancelled, user=stranded.user, status="confirmed"
        )
        booked = self._profile("real@example.com", name="Booked")
        EventRegistration.objects.create(
            event=self.event, user=booked.user, status="confirmed"
        )

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "upcoming"})

        self.assertEqual(self._names(resp), {"Booked"})

    def test_submission_assigned_to_a_deactivated_coach_counts_as_unowned(self):
        """`coach_required` turns a deactivated coach away from every coach
        view, so nobody can act on their submissions."""
        from crush_lu.models import CrushCoach, ProfileSubmission

        gone_user = self._user("gonecoach@example.com", first_name="Gone")
        gone_coach = CrushCoach.objects.create(user=gone_user, is_active=False)

        orphaned = self._profile("orphaned@example.com", name="Orphaned")
        ProfileSubmission.objects.create(
            profile=orphaned, status="pending", coach=gone_coach
        )
        held = self._profile("held@example.com", name="Held")
        ProfileSubmission.objects.create(
            profile=held, status="pending", coach=self.other_coach
        )

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._list_url(), {"signal": "unowned"})

        self.assertIn("Orphaned", self._names(resp))
        self.assertNotIn("Held", self._names(resp))

    def test_non_coach_is_redirected(self):
        member = self._user("member@example.com")
        self.client.force_login(member)

        resp = self.client.get(self._list_url())

        self.assertEqual(resp.status_code, 302)


@override_settings(**CRUSH_LU_URL_SETTINGS)
class CoachVerifyMemberTests(CoachUnverifiedBase):
    def _url(self, profile):
        return reverse(
            "crush_lu:coach_verify_member", kwargs={"user_id": profile.user_id}
        )

    def _post(self, profile, **extra):
        data = {"confirm": "yes"}
        data.update(extra)
        return self.client.post(self._url(profile), data)

    def test_verifies_a_profile_with_no_submission_and_writes_an_audit_row(self):
        from crush_lu.models import ProfileSubmission

        profile = self._profile("nosub@example.com")
        self.client.force_login(self.coach_user)

        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            resp = self._post(profile, reason="Checked ID at the door")

        self.assertEqual(resp.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "verified")
        self.assertTrue(profile.is_approved)
        self.assertIsNotNone(profile.approved_at)
        # `admin`, never `coach_event`: `has_attended_event` reads the latter
        # as proof the member stood in front of a coach at a door.
        self.assertEqual(profile.verification_method, "admin")
        self.assertFalse(profile.has_attended_event)

        submission = ProfileSubmission.objects.get(profile=profile)
        self.assertEqual(submission.status, "approved")
        self.assertEqual(submission.coach_id, self.coach.id)
        self.assertIn("Verified from the coach panel by Cam", submission.coach_notes)
        self.assertIn("Checked ID at the door", submission.coach_notes)

        # Referral credit + welcome email must run, same as at the door.
        side.assert_called_once()

    def test_approves_an_open_submission_in_place(self):
        from crush_lu.models import ProfileSubmission

        profile = self._profile("open@example.com")
        submission = ProfileSubmission.objects.create(profile=profile, status="pending")

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        self.assertEqual(ProfileSubmission.objects.filter(profile=profile).count(), 1)
        submission.refresh_from_db()
        self.assertEqual(submission.status, "approved")
        self.assertTrue(submission.review_call_completed)
        self.assertEqual(submission.coach_id, self.coach.id)

    def test_expired_latest_row_is_not_reopened(self):
        """The expired story stays closed; a fresh terminal row records this."""
        from crush_lu.models import ProfileSubmission

        profile = self._profile("expired@example.com")
        expired = ProfileSubmission.objects.create(profile=profile, status="expired")

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        expired.refresh_from_db()
        self.assertEqual(expired.status, "expired")
        fresh = ProfileSubmission.objects.filter(profile=profile, status="approved")
        self.assertEqual(fresh.count(), 1)
        self.assertEqual(fresh.first().coach_id, self.coach.id)

    def test_rejected_profile_is_overturned_and_noted(self):
        from crush_lu.models import ProfileSubmission

        profile = self._profile("rejected@example.com", status="rejected")
        submission = ProfileSubmission.objects.create(
            profile=profile, status="rejected"
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "verified")
        submission.refresh_from_db()
        self.assertEqual(submission.status, "approved")
        self.assertIn("rejection overturned", submission.coach_notes)

    def test_missing_confirmation_verifies_nobody(self):
        profile = self._profile("noconfirm@example.com")

        self.client.force_login(self.coach_user)
        resp = self.client.post(self._url(profile), {})

        self.assertEqual(resp.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")

    def test_get_is_rejected(self):
        profile = self._profile("getme@example.com")

        self.client.force_login(self.coach_user)
        resp = self.client.get(self._url(profile))

        self.assertEqual(resp.status_code, 405)
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")

    def test_premium_member_is_reserved_for_their_own_coach(self):
        from crush_lu.models import PremiumMembership

        profile = self._profile("premium@example.com")
        profile.assigned_coach = self.other_coach
        profile.assigned_coach_at = timezone.now()
        profile.save(update_fields=["assigned_coach", "assigned_coach_at"])
        PremiumMembership.objects.create(
            user=profile.user, coach=self.other_coach, status="active"
        )

        self.client.force_login(self.coach_user)
        self._post(profile)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")

        # Their own coach may.
        self.client.force_login(self.other_coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "verified")

    def test_already_verified_is_idempotent_and_runs_no_side_effects(self):
        profile = self._profile("done@example.com", status="verified")
        profile.is_approved = True
        profile.verification_method = "luxid"
        profile.save(update_fields=["is_approved", "verification_method"])

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            self._post(profile)

        profile.refresh_from_db()
        # The winning path keeps its method — a second claim must not rewrite
        # a LuxID verification as a manual one.
        self.assertEqual(profile.verification_method, "luxid")
        side.assert_not_called()

    def test_inactive_or_banned_members_cannot_be_verified(self):
        """The list hides them; this endpoint reloads any user by id.

        Without the guard a stale link or a hand-made POST verifies a
        deactivated or banned account and then pays its referrer and mails it
        a welcome. A ban leaves the profile row in place, so `is_active` alone
        does not cover it.
        """
        inactive = self._profile("gone@example.com", is_active=False)
        banned = self._profile("banned@example.com")
        self.UserDataConsent.objects.filter(user=banned.user).update(
            crushlu_banned=True
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            self._post(inactive)
            self._post(banned)

        for profile in (inactive, banned):
            profile.refresh_from_db()
            self.assertEqual(profile.verification_status, "pending")
        side.assert_not_called()

    def test_open_recontact_row_is_closed_and_credited_to_the_acting_coach(self):
        """`coach_profiles` selects recontact rows and never excludes verified
        profiles, so an open one keeps the member in the old coach's queue.
        And `coach_verification_history` filters on `coach=coach`, so leaving
        the previous owner on the row hides the decision from whoever made it.
        """
        from crush_lu.models import ProfileSubmission

        profile = self._profile("recontact@example.com")
        submission = ProfileSubmission.objects.create(
            profile=profile, status="recontact_coach", coach=self.other_coach
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        self.assertEqual(ProfileSubmission.objects.filter(profile=profile).count(), 1)
        submission.refresh_from_db()
        self.assertEqual(submission.status, "approved")
        self.assertEqual(submission.coach_id, self.coach.id)

    def test_outlook_contact_is_resynced_after_the_atomic_claim(self):
        """`claim_profile_verification` is a QuerySet.update() and skips
        post_save, so the contact would keep serving the old status."""
        profile = self._profile("outlook@example.com")

        self.client.force_login(self.coach_user)
        with (
            patch("crush_lu.views_coach._run_post_verification_side_effects"),
            patch("crush_lu.signals.sync_profile_to_outlook") as sync,
        ):
            self._post(profile)

        sync.assert_called_once()
        self.assertEqual(sync.call_args.kwargs["instance"].pk, profile.pk)

    def test_member_without_crushlu_consent_cannot_be_verified(self):
        """The list filters these out; the endpoint must refuse independently.

        Otherwise a posted id verifies somebody who abandoned the consent
        screen, writing an approval record and mailing them about it.
        """
        profile = self._profile("noconsent@example.com")
        self.UserDataConsent.objects.filter(user=profile.user).update(
            crushlu_consent_given=False
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            self._post(profile)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")
        side.assert_not_called()

    def test_coach_cannot_verify_their_own_profile(self):
        """Same rule the door enforces in `_attest_and_record_photo`.

        A coach who is also a member sees their own unverified profile on the
        team-wide list, one "Open profile" click from the form — so this needs
        no guessed URL.
        """
        own = self.CrushProfile.objects.create(
            user=self.coach_user,
            show_full_name=False,
            gender="M",
            location="Luxembourg",
            verification_status="pending",
            photo_1="users/1/photos/a.jpg",
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            self._post(own)

        own.refresh_from_db()
        self.assertEqual(own.verification_status, "pending")
        side.assert_not_called()

    def test_member_without_a_photo_cannot_be_verified(self):
        """The coach signs "their photo matches" — impossible with no photo."""
        profile = self._profile("nophoto@example.com", photo=False)

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects") as side:
            self._post(profile)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")
        side.assert_not_called()

    def test_already_approved_row_records_the_repair_without_rewriting_it(self):
        """A verified/approved split is repaired, not overwritten.

        The earlier approval really happened, so its coach and `reviewed_at`
        stay put; the repair is appended so the form's promise that the note
        reaches the review record still holds.
        """
        from crush_lu.models import ProfileSubmission

        profile = self._profile("split@example.com")
        reviewed_at = timezone.now() - timedelta(days=3)
        submission = ProfileSubmission.objects.create(
            profile=profile,
            status="approved",
            coach=self.other_coach,
            reviewed_at=reviewed_at,
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile, reason="Split state repair")

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "verified")
        self.assertEqual(ProfileSubmission.objects.filter(profile=profile).count(), 1)

        submission.refresh_from_db()
        self.assertEqual(submission.coach_id, self.other_coach.id)
        self.assertEqual(submission.reviewed_at, reviewed_at)
        self.assertIn("Split state repair", submission.coach_notes)
        self.assertIn("original approval record is unchanged", submission.coach_notes)

    def test_future_booked_screening_slot_is_released(self):
        """`coach_action_queue` lists future booked slots regardless of the
        submission's status, so one left booked keeps showing the original
        coach a call for an already-verified member."""
        from crush_lu.models import ProfileSubmission, ScreeningSlot

        profile = self._profile("slot@example.com")
        submission = ProfileSubmission.objects.create(
            profile=profile, status="pending", coach=self.other_coach
        )
        start_at = timezone.now() + timedelta(days=1)
        slot = ScreeningSlot.objects.create(
            coach=self.other_coach,
            submission=submission,
            status="booked",
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
        )
        past_start = timezone.now() - timedelta(days=1)
        past_slot = ScreeningSlot.objects.create(
            coach=self.other_coach,
            submission=submission,
            status="booked",
            start_at=past_start,
            end_at=past_start + timedelta(minutes=30),
        )

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            self._post(profile)

        slot.refresh_from_db()
        self.assertEqual(slot.status, "cancelled")
        self.assertEqual(slot.cancelled_reason, "verified_by_coach")

        # A slot in the past is history, not an appointment to release.
        past_slot.refresh_from_db()
        self.assertEqual(past_slot.status, "booked")

        submission.refresh_from_db()
        self.assertTrue(
            any(
                a.get("type") == "booking_cancelled"
                for a in (submission.system_actions or [])
            )
        )

    def test_non_coach_cannot_verify(self):
        profile = self._profile("target@example.com")
        self.client.force_login(self._user("nosy@example.com"))

        resp = self.client.post(self._url(profile), {"confirm": "yes"})

        self.assertEqual(resp.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "pending")


class CoachUnverifiedHostRoutingTests(CoachUnverifiedBase):
    """Reach the page the way production does: by Host header.

    Deliberately without the `ROOT_URLCONF` override the other classes use.
    Those exercise the view; this exercises `DomainURLRoutingMiddleware`
    swapping `request.urlconf` per host, which is what actually resolves
    `/coach/unverified/` on crush.lu. `reverse()` cannot stand in for it — it
    resolves against the default URLconf, where crush_lu is mounted under
    `/crush/`, so a route that 404s on the real host would still pass.

    The literal path carries `/en/` because every crush_lu route lives inside
    `i18n_patterns(..., prefix_default_language=True)`.
    """

    def test_page_resolves_on_the_crush_host(self):
        self._profile("host@example.com", name="HostRouted")

        self.client.force_login(self.coach_user)
        resp = self.client.get("/en/coach/unverified/", HTTP_HOST="crush.lu")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("HostRouted", self._names(resp))

    def test_verify_endpoint_resolves_on_the_crush_host(self):
        profile = self._profile("hostverify@example.com")

        self.client.force_login(self.coach_user)
        with patch("crush_lu.views_coach._run_post_verification_side_effects"):
            resp = self.client.post(
                f"/en/coach/member/{profile.user_id}/verify/",
                {"confirm": "yes"},
                HTTP_HOST="crush.lu",
            )

        self.assertEqual(resp.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, "verified")

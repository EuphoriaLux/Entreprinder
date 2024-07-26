document.addEventListener('DOMContentLoaded', function() {
    const swipeContainer = document.getElementById('swipe-container');
    const likeButton = document.getElementById('like');
    const dislikeButton = document.getElementById('dislike');
    const buttonsContainer = document.querySelector('.swipe-buttons');

    let currentCard = swipeContainer.querySelector('.profile-card');
    let hammer = new Hammer(swipeContainer);
    let isSwipeInProgress = false;

    setupSwipe();

    function setupSwipe() {
        hammer.on('pan', handlePan);
        hammer.on('panend', handlePanEnd);
    }

    function handlePan(event) {
        if (isSwipeInProgress) return;
        const card = swipeContainer.querySelector('.profile-card');
        if (!card) return;
        
        const xPos = event.deltaX;
        const rotate = xPos / 10;

        card.style.transform = `translateX(${xPos}px) rotate(${rotate}deg)`;
        card.style.transition = 'none';
    }

    function handlePanEnd(event) {
        if (isSwipeInProgress) return;
        const card = swipeContainer.querySelector('.profile-card');
        if (!card) return;

        const threshold = 150;
        let action = 'reset';

        if (event.deltaX > threshold) {
            action = 'like';
        } else if (event.deltaX < -threshold) {
            action = 'dislike';
        }

        if (action === 'reset') {
            card.style.transform = '';
        } else {
            const endX = action === 'like' ? window.innerWidth : -window.innerWidth;
            card.style.transform = `translateX(${endX}px) rotate(${event.deltaX / 10}deg)`;
        }

        card.style.transition = 'transform 0.5s';

        if (action !== 'reset') {
            isSwipeInProgress = true;
            setTimeout(() => {
                swipeAction(action);
                isSwipeInProgress = false;
            }, 500);
        }
    }

    function swipeAction(action) {
        const card = swipeContainer.querySelector('.profile-card');
        if (!card) return;

        const profileId = card.dataset.profileId;

        fetch('/swipe-action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                profile_id: profileId,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'match') {
                showMatchView(data.match_profile, data.next_profile);
            } else if (data.next_profile) {
                updateProfileCard(data.next_profile);
            } else {
                showNoMoreProfiles();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }

    function updateProfileCard(profile) {
        const profilePicture = profile.profile_picture ? profile.profile_picture : '/static/images/default-profile.png';
        const newCard = document.createElement('div');
        newCard.className = 'profile-card';
        newCard.dataset.profileId = profile.id;
        newCard.innerHTML = `
            <img src="${profilePicture}" alt="${profile.full_name}'s profile picture" class="profile-picture">
            <div class="profile-info">
                <h2>${profile.full_name}</h2>
                <p><strong>Industry:</strong> ${profile.industry || 'N/A'}</p>
                <p><strong>Company:</strong> ${profile.company || 'N/A'}</p>
                <p>${profile.bio || 'No bio available.'}</p>
            </div>
        `;
        
        swipeContainer.innerHTML = '';
        swipeContainer.appendChild(newCard);
        buttonsContainer.style.display = 'flex';

        currentCard = newCard;
        setupSwipe();
    }

    function showMatchView(matchProfile, nextProfile) {
        const matchView = document.createElement('div');
        matchView.className = 'match-view';
        matchView.innerHTML = `
            <div class="match-content">
                <h2>It's a Match!</h2>
                <div class="match-profiles">
                    <img src="${currentCard.querySelector('.profile-picture').src}" alt="Your profile" class="match-profile-pic">
                    <img src="${matchProfile.profile_picture || '/static/images/default-profile.png'}" alt="${matchProfile.full_name}'s profile" class="match-profile-pic">
                </div>
                <p>You and ${matchProfile.full_name} have liked each other!</p>
                <button id="continueSwipingBtn" class="btn btn-primary">Continue Swiping</button>
            </div>
        `;
        
        swipeContainer.innerHTML = '';
        swipeContainer.appendChild(matchView);
        buttonsContainer.style.display = 'none';

        document.getElementById('continueSwipingBtn').addEventListener('click', () => {
            if (nextProfile) {
                updateProfileCard(nextProfile);
            } else {
                showNoMoreProfiles();
            }
        });
    }

    function showNoMoreProfiles() {
        swipeContainer.innerHTML = `
            <div class="profile-card">
                <div class="profile-info text-center">
                    <h2>No more profiles</h2>
                    <p>Check back later for new matches!</p>
                </div>
            </div>
        `;
        buttonsContainer.style.display = 'none';
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    if (likeButton) likeButton.addEventListener('click', () => swipeAction('like'));
    if (dislikeButton) dislikeButton.addEventListener('click', () => swipeAction('dislike'));
});
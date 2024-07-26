document.addEventListener('DOMContentLoaded', function() {
    const swipeContainer = document.getElementById('swipe-container');
    const likeButton = document.getElementById('like');
    const dislikeButton = document.getElementById('dislike');
    const buttonsContainer = document.querySelector('.swipe-buttons');

    let currentCard = null;
    let hammer = null;
    let isSwipeInProgress = false;

    // Load the initial profile
    if (initialProfile) {
        updateProfileCard(initialProfile);
    } else {
        showNoMoreProfiles();
    }

    function setupSwipe() {
        if (currentCard) {
            // Destroy previous Hammer instance if it exists
            if (hammer) {
                hammer.destroy();
            }
            // Initialize new Hammer instance
            hammer = new Hammer(currentCard);
            hammer.on('pan', handlePan);
            hammer.on('panend', handlePanEnd);
        }
    }

    function handlePan(event) {
        if (isSwipeInProgress || !currentCard) return;
        
        const xPos = event.deltaX;
        const rotate = xPos / 10;

        currentCard.style.transform = `translateX(${xPos}px) rotate(${rotate}deg)`;
        currentCard.style.transition = 'none';
    }

    function handlePanEnd(event) {
        if (isSwipeInProgress || !currentCard) return;

        const threshold = 150;
        let action = 'reset';

        if (event.deltaX > threshold) {
            action = 'like';
        } else if (event.deltaX < -threshold) {
            action = 'dislike';
        }

        if (action === 'reset') {
            currentCard.style.transform = '';
        } else {
            const endX = action === 'like' ? window.innerWidth : -window.innerWidth;
            currentCard.style.transform = `translateX(${endX}px) rotate(${event.deltaX / 10}deg)`;
        }

        currentCard.style.transition = 'transform 0.5s';

        if (action !== 'reset') {
            isSwipeInProgress = true;
            setTimeout(() => {
                swipeAction(action);
                isSwipeInProgress = false;
            }, 500);
        }
    }

    function swipeAction(action) {
        if (!currentCard) return;
    
        const profileId = currentCard.dataset.profileId;
    
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
                if (data.match_profile) {
                    const currentUserPicture = currentCard.querySelector('.profile-picture').src;
                    showMatchView(data.match_profile, data.next_profile, currentUserPicture);
                } else {
                    console.error('Match found but no match_profile data received');
                    showErrorModal('An error occurred while processing the match. Please try again.');
                }
            } else if (data.status === 'success') {
                if (data.next_profile) {
                    updateProfileCard(data.next_profile);
                } else {
                    redirectToNoMoreProfiles();
                }
            } else if (data.status === 'no_more_profiles') {
                redirectToNoMoreProfiles();
            } else {
                console.error('Unexpected response status:', data.status);
                showErrorModal('An unexpected error occurred. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorModal('An error occurred. Please try again.');
        });
    }

    function showMatchView(matchProfile, nextProfile) {
        if (!matchProfile) {
            console.error('No match profile data provided to showMatchView');
            return;
        }
    
        console.log('Match profile data:', matchProfile);
        console.log('Current user picture:', currentUserPicture);
    
        const matchView = document.createElement('div');
        matchView.className = 'match-view';
        matchView.innerHTML = `
            <div class="match-content">
                <h2>It's a Match!</h2>
                <div class="match-profiles">
                    <img src="${currentUserPicture}" alt="Your profile" class="match-profile-pic">
                    <img src="${matchProfile.profile_picture}" alt="${matchProfile.full_name}'s profile" class="match-profile-pic">
                </div>
                <p>You and ${matchProfile.full_name} have liked each other!</p>
                <button id="continueSwipingBtn" class="btn btn-primary">Continue Swiping</button>
            </div>
        `;
        
        swipeContainer.innerHTML = '';
        swipeContainer.appendChild(matchView);
        if (buttonsContainer) buttonsContainer.style.display = 'none';
    
        document.getElementById('continueSwipingBtn').addEventListener('click', () => {
            if (nextProfile) {
                updateProfileCard(nextProfile);
            } else {
                redirectToNoMoreProfiles();
            }
        });
    }

    function updateProfileCard(profile) {
        if (!profile) {
            console.error('No profile data provided to updateProfileCard');
            showErrorModal('An error occurred while loading the next profile. Please try again.');
            return;
        }

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
        if (buttonsContainer) buttonsContainer.style.display = 'flex';

        currentCard = newCard;
        setupSwipe();
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
        if (buttonsContainer) buttonsContainer.style.display = 'none';
    }

    function showErrorModal(message) {
        const modal = document.createElement('div');
        modal.className = 'error-modal';
        modal.innerHTML = `
            <div class="error-content">
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="this.closest('.error-modal').remove()">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
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

    function redirectToNoMoreProfiles() {
        window.location.href = '{% url "entreprinder:no_more_profiles" %}';
    }

    if (likeButton) likeButton.addEventListener('click', () => swipeAction('like'));
    if (dislikeButton) dislikeButton.addEventListener('click', () => swipeAction('dislike'));
});
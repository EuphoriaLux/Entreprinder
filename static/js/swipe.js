document.addEventListener('DOMContentLoaded', (event) => {
    const container = document.getElementById('swipe-container');
    const likeBtn = document.getElementById('like');
    const dislikeBtn = document.getElementById('dislike');

    let currentCard = container.querySelector('.profile-card');

    function swipe(action) {
        if (!currentCard) {
            console.log('No more profiles to show');
            return;
        }

        const profileId = currentCard.getAttribute('data-profile-id');

        fetch('/swipe-action/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                profile_id: profileId,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.status === 'match') {
                alert('It\'s a match!');
            }
            currentCard.style.transform = `translateX(${action === 'like' ? '' : '-'}100%)`;
            setTimeout(() => {
                currentCard.remove();
                currentCard = container.querySelector('.profile-card');
                if (!currentCard) {
                    container.innerHTML = '<p>No more profiles to show!</p>';
                }
            }, 300);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    }

    likeBtn.addEventListener('click', () => swipe('like'));
    dislikeBtn.addEventListener('click', () => swipe('dislike'));

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
});
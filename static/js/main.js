// Animate repo submit button
document.getElementById('analyze-repo-form').addEventListener('submit', function() {
    anime({
        targets: '.btn-primary',
        scale: [1, 1.08, 1],
        boxShadow: [
            '0 0 20px #3f88ff',
            '0 0 50px #2ce0ff',
            '0 0 20px #3f88ff'
        ],
        easing: 'easeInOutSine',
        duration: 800
    });
});

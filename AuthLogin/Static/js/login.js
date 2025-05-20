document.addEventListener('DOMContentLoaded', function() {
    // Create floating ball
    const ball = document.createElement('div');
    ball.className = 'floating-ball';
    document.querySelector('.background-container').appendChild(ball);
    
    // Interactive background with ball movement
    document.addEventListener('mousemove', function(e) {
        const x = e.clientX;
        const y = e.clientY;
        
        // Move the ball with a slight delay for smooth effect
        setTimeout(() => {
            ball.style.transform = `translate(${x - 40}px, ${y - 40}px)`;
        }, 100);
        
        // Subtle background movement
        const background = document.querySelector('.moving-background');
        const xPercent = e.clientX / window.innerWidth;
        const yPercent = e.clientY / window.innerHeight;
        
        background.style.transform = `translate(${xPercent * 20}px, ${yPercent * 20}px) scale(1.1)`;
    });
    
    // Password visibility toggle 
    const passwordInput = document.getElementById('password');
    const toggleButton = document.querySelector('.toggle-password');
    const eyeIcon = document.querySelector('.eye-icon');
    
    // Initialize eye icon state
    eyeIcon.classList.add('hidden');
    
    // Show/hide toggle button based on password field content
    passwordInput.addEventListener('input', function() {
        if (this.value.length > 0) {
            toggleButton.style.display = 'block';
        } else {
            toggleButton.style.display = 'none';
        }
    });
    
    // Toggle password visibility
    toggleButton.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent any default behavior
        
        if (passwordInput.type === 'password') {
            
            passwordInput.type = 'text';
            
            eyeIcon.classList.remove('hidden');
            eyeIcon.classList.add('visible');
        } else {
            passwordInput.type = 'password';
            eyeIcon.classList.remove('visible');
            eyeIcon.classList.add('hidden');
        }
    });
    
    // Dynamic input fields - clear placeholder on focus
    const dynamicInputs = document.querySelectorAll('.dynamic-input');
    
    dynamicInputs.forEach(input => {
        const originalPlaceholder = input.placeholder;
        
        input.addEventListener('focus', function() {
            this.placeholder = '';
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.placeholder = originalPlaceholder;
            }
        });
    });
    
    // Add some random floating elements in the background for visual interest
    const backgroundContainer = document.querySelector('.background-container');
    const colors = ['#39bfb2', '#F2CE16', '#F29D35', '#F28627'];
    
    for (let i = 0; i < 10; i++) {
        const floatingElement = document.createElement('div');
        const size = Math.random() * 30 + 10;
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        floatingElement.style.position = 'absolute';
        floatingElement.style.width = `${size}px`;
        floatingElement.style.height = `${size}px`;
        floatingElement.style.backgroundColor = color;
        floatingElement.style.borderRadius = '50%';
        floatingElement.style.opacity = '0.2';
        floatingElement.style.left = `${Math.random() * 100}%`;
        floatingElement.style.top = `${Math.random() * 100}%`;
        floatingElement.style.zIndex = '-1';
        floatingElement.style.animation = `float ${Math.random() * 10 + 10}s linear infinite`;
        
        backgroundContainer.appendChild(floatingElement);
    }
    
    // Add floating animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0% { transform: translate(0, 0) rotate(0deg); }
            25% { transform: translate(10px, 10px) rotate(90deg); }
            50% { transform: translate(0, 20px) rotate(180deg); }
            75% { transform: translate(-10px, 10px) rotate(270deg); }
            100% { transform: translate(0, 0) rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
});
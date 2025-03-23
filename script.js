document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            button.classList.add('clicked');
            setTimeout(() => button.classList.remove('clicked'), 200);
        });
    });

    const gridItems = document.querySelectorAll('.grid-item');
    gridItems.forEach((item, index) => {
        item.style.opacity = '0';
        setTimeout(() => {
            item.style.transition = 'opacity 0.3s ease, transform 0.2s ease';
            item.style.opacity = '1';
            item.style.transform = 'scale(1)';
        }, index * 50); // Staggered fade-in effect
    });

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.opacity = '0';
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '1';
        }, 100);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.head.insertAdjacentHTML('beforeend', `
    <style>
        .btn-primary.clicked, .btn-secondary.clicked {
            transform: scale(0.95);
        }
        .grid-item.highlight {
            background-color: #e3f2fd;
            border-color: #6b48ff;
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }
    </style>
`);
window.addEventListener('load', () => {
    updateScrollProgress();
    initializeHeroSlideshow();
});

window.addEventListener('scroll', updateScrollProgress);
window.addEventListener('resize', updateScrollProgress);

function updateScrollProgress() {
    const progressElement = document.getElementById('scroll-progress-fill');
    if (!progressElement) return;

    const scrollTop = window.scrollY;
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const width = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    progressElement.style.width = `${width}%`;
}

function initializeHeroSlideshow() {
    const slides = document.querySelectorAll('.hero-section .slide');
    const indicators = document.querySelectorAll('.hero-section .indicator');
    if (!slides.length || !indicators.length) return;

    let activeIndex = 0;
    let slideTimeout;

    const activateSlide = (index) => {
        slides.forEach((slide, idx) => {
            slide.classList.toggle('active', idx === index);
        });
        indicators.forEach((indicator, idx) => {
            indicator.classList.toggle('active', idx === index);
        });
        activeIndex = index;
        resetSlideshowTimeout();
    };

    const nextSlide = () => {
        const nextIndex = (activeIndex + 1) % slides.length;
        activateSlide(nextIndex);
    };

    const resetSlideshowTimeout = () => {
        if (slideTimeout) clearTimeout(slideTimeout);
        slideTimeout = setTimeout(nextSlide, 5000);
    };

    indicators.forEach((indicator, idx) => {
        indicator.addEventListener('click', () => {
            activateSlide(idx);
        });
    });

    activateSlide(activeIndex);
}

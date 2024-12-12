document.addEventListener('DOMContentLoaded', function () {
    interface Tagline {
        text: string;
        bgImage: string;
        color: string;
    }

    const taglines: Tagline[] = [
        { text: 'Empower Your Future', bgImage: "{% static 'images/background_image_1.png' %}", color: 'red' },
        { text: 'Innovate and Lead', bgImage: "{% static 'images/background_image_2.png' %}", color: 'blue' },
        { text: 'Connect and Collaborate', bgImage: "{% static 'images/background_image_3.png' %}", color: 'green' },
        { text: 'Discover Your Potential', bgImage: "{% static 'images/background_image_4.png' %}", color: 'purple' },
        { text: 'Achieve Excellence', bgImage: "{% static 'images/background_image_5.png' %}", color: 'orange' }
    ];

    let index = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingSpeed = 100; // Typing speed in milliseconds

    const section = document.getElementById('dynamic-section') as HTMLElement;
    const taglineElement = document.getElementById('dynamic-tagline') as HTMLElement;

    function typeTagline() {
        const currentTagline = taglines[index];
        const fullText = currentTagline.text;

        if (isDeleting) {
            charIndex--;
            taglineElement.textContent = fullText.substring(0, charIndex);
        } else {
            charIndex++;
            taglineElement.textContent = fullText.substring(0, charIndex);
        }

        // Adjust font size and color dynamically
        const fontSize = isDeleting ? 2 + (charIndex / fullText.length) * 2 : 1 + (charIndex / fullText.length) * 2;
        taglineElement.style.fontSize = `${fontSize}em`;
        taglineElement.style.color = currentTagline.color;

        // Handle typing and deleting logic
        if (!isDeleting && charIndex === fullText.length) {
            // Pause before deleting
            setTimeout(() => isDeleting = true, 2000);
        } else if (isDeleting && charIndex === 0) {
            // Move to next tagline
            isDeleting = false;
            index = (index + 1) % taglines.length;
            section.style.backgroundImage = `url(${currentTagline.bgImage})`;
        }

        // Recursively call function with variable speed
        const delay = isDeleting ? typingSpeed / 2 : typingSpeed;
        setTimeout(typeTagline, delay);
    }

    // Start the typing effect
    typeTagline();
});

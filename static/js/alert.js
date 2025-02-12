class Alert {
    constructor() {
        this.messageQueue = [];
        this.activeMessage = null;
        this.lastMessages = []
    }

    showBar({ message, duration = 5, error = false }) {
        const now = Date.now();
        const isRecent = this.lastMessages.some(
            (lastMessage) =>
                now - lastMessage.timestamp < 3000 &&
                lastMessage.message === message &&
                lastMessage.error === error
        );

        if (!isRecent) {
            this.messageQueue.push({ message, duration, error });
            this.lastMessages.push({ message, timestamp: now, error });

            this.lastMessages = this.lastMessages.filter(
                (msg) => now - msg.timestamp < 3000
            );

            if (!this.activeMessage) {
                this.displayNextMessage();
            }
        }
    }
    displayNextMessage() {
        if (this.messageQueue.length === 0) {
            return;
        }

        const { message, duration, error } = this.messageQueue.shift();
        this.activeMessage = { message, error };

        let infoBar = document.getElementById('info-bar');
        if (!infoBar) {
            infoBar = document.createElement('div');
            infoBar.id = 'info-bar';
            infoBar.style.width = '100%';
            infoBar.style.zIndex = '1000';
            infoBar.style.display = 'none';
            document.body.appendChild(infoBar);
        }

        infoBar.className = `bg-${error ? 'danger' : 'success'} text-white d-flex justify-content-between align-items-center fixed-top py-2 `;

        const messageContent = document.createElement('span');
        messageContent.className = 'flex-grow-1 text-center';
        messageContent.textContent = message;

        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'd-flex align-items-center';

        const countdownContainer = document.createElement('div');
        countdownContainer.className = 'position-relative d-inline-block me-2'; // Wrapper for both button and svg

        const closeButton = document.createElement('button');
        closeButton.className ='btn btn-close btn-close-white position-absolute top-50 start-50 translate-middle'; // 'btn text-white infobar-close-button';
        closeButton.style.position = 'absolute';
        closeButton.style.top = '50%';
        closeButton.style.left = '50%';
        closeButton.style.transform = 'translate(-50%, -50%)';
        closeButton.style.zIndex = '1';
        closeButton.onclick = () => this.closeBar(infoBar);


        const countdownCircleWrapper = document.createElement('div');
        countdownCircleWrapper.className = 'w-100 h-100 rounded-circle border-2 border-white';

        const countdownSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        countdownSvg.setAttribute('class', 'countdown-svg');
        countdownSvg.setAttribute('width', '40');
        countdownSvg.setAttribute('height', '40');
        countdownSvg.setAttribute('viewBox', '0 0 40 40');

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '20');
        circle.setAttribute('cy', '20');
        circle.setAttribute('r', '18');
        circle.style.animation = `countdown ${duration}s linear forwards`;
        countdownSvg.appendChild(circle);
        countdownCircleWrapper.appendChild(countdownSvg);

        countdownContainer.appendChild(countdownCircleWrapper);
        countdownContainer.appendChild(closeButton);

        buttonContainer.appendChild(countdownContainer);

        infoBar.innerHTML = '';
        infoBar.appendChild(messageContent);
        infoBar.appendChild(buttonContainer);
        infoBar.style.display = 'block';
        infoBar?.classList.remove('d-none');

        setTimeout(() => this.closeBar(infoBar), duration * 1000);
    }

    closeBar(infoBar) {
        if (infoBar) {
            infoBar.style.display = 'none';
            infoBar.classList.add('d-none');
        }
        this.activeMessage = null;
        this.displayNextMessage();
    }
}
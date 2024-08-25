document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const dropZone = document.getElementById('drop-zone');
    const hiddenFileInput = document.getElementById('hidden-file-input');

    chatForm.addEventListener('submit', handleSubmit);
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleDrop);
    document.addEventListener('paste', handlePaste);
    userInput.addEventListener('keydown', handleKeyDown);

    function handleSubmit(e) {
        e.preventDefault();
        sendMessage();
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, true);
            sendMessageToServer(message);
            userInput.value = '';
        } else {
            alert('נא להקליד הודעה לפני השליחה.');
        }
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        const files = e.dataTransfer.files;
        if (files.length) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                sendImageToServer(file);
            } else {
                alert('נא להעלות קובץ תמונה בלבד.');
            }
        }
    }

    function handlePaste(e) {
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const blob = items[i].getAsFile();
                sendImageToServer(blob);
                e.preventDefault();
                return;
            }
        }
    }

    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessageToServer(message) {
        const formData = new FormData();
        formData.append('message', message);

        fetch('/chat', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            addMessage(data.response, false);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('אירעה שגיאה בעת שליחת ההודעה.', false);
        });
    }

    function sendImageToServer(file) {
        addMessage('מעלה תמונה...', true);

        const formData = new FormData();
        formData.append('image', file);

        fetch('/chat', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            addMessage(data.response, false);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('אירעה שגיאה בעת העלאת התמונה.', false);
        });
    }

    // Optional: Add click event to drop zone to trigger file input
    dropZone.addEventListener('click', () => {
        hiddenFileInput.click();
    });

    hiddenFileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            const file = e.target.files[0];
            if (file.type.startsWith('image/')) {
                sendImageToServer(file);
            } else {
                alert('נא להעלות קובץ תמונה בלבד.');
            }
        }
    });
});
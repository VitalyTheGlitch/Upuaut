function Modal(modal_selector) {
    const modal = document.querySelector(modal_selector);
    const header = modal.querySelector('.modal-header');
    const body = modal.querySelector('.modal-body');
    const buttonClose = modal.querySelector('.close-modal');

    buttonClose.addEventListener('click', closeModal, false);
    modal.addEventListener('click', (e) => e.stopPropagation());

    function setHeader(text) {
        header.firstChild.nodeValue = text;
    }

    function setBody(text) {
        body.innerHTML = text;
    }

    function openModal(e) {
        e && e.stopPropagation();

        modal.classList.add('opened');
        modal.classList.remove('closed');
    }

    function closeModal() {
        modal.classList.remove('opened');
        modal.classList.add('closed');
    }

    this.setHeader = setHeader;
    this.setBody = setBody;
    this.open = openModal;
    this.close = closeModal;
}

window.messages = new Modal('.messages');

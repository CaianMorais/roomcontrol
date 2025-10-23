import { showAlert } from '../alerts.js';
import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

// edit_guests.html & new_guests.html
Inputmask({
    mask: ['999.999.999-99'],
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
}).mask("#cpf");

Inputmask({
    mask: ['(99) 99999-9999', '(99) 9999-9999'],
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
}).mask("#phone_number");

// edit_guests.html
document.addEventListener("DOMContentLoaded", function () {
    const deleteLinks = document.querySelectorAll(".btn-delete-guest");

    deleteLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;

            showAlert(
                `Você tem certeza?`,
                `Essa ação é irreversível!`,
                'warning'
            ).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});
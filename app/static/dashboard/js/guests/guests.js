import { showAlert } from '../alerts.js';
import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

// edit_guests.html & new_guests.html
Inputmask("999.999.999-99", {
    rightAlign: false,
    removeMaskOnSubmit: true,
    autoUnmask: true,
}).mask("#cpf");

Inputmask("(99) 99999-9999", {
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    autoUnmask: true,
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
                `As reservas ativas associadas a este hóspede serão canceladas e os quartos serão liberados.`,
                'warning'
            ).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});
import { showAlert } from '../alerts.js';
import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

Inputmask({
    mask: ['999.999.999-99'],
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    unmaskAsNumber: true,
}).mask("#cpf");

document.addEventListener("DOMContentLoaded", function () {
    const updateBtn = document.querySelectorAll(".btn-update-reservation");
    const cancelBtn = document.querySelectorAll(".btn-cancel-reservation");

    updateBtn.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;
            showAlert("Atualizar a situação da reserva?", "Essa ação é irreversível.", "question")
            .then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
    cancelBtn.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;
            showAlert("Cancelar esta reserva?", "Essa ação é irreversível.", "warning")
            .then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});
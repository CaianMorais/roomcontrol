import { showAlert } from '../alerts.js';
import Inputmask from "https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.9/inputmask.es6.min.js";

Inputmask("99.999.999/9999-99", {
    rightAlign: false,
    removeMaskOnSubmit: true,
    autoUnmask: true,
}).mask("#cnpj");

Inputmask("(99) 99999-9999", {
    keepStatic: true,
    rightAlign: false,
    removeMaskOnSubmit: true,
    autoUnmask: true,
}).mask("#phone_number");

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('hotelProfileForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            console.log("phone_number", form.phone_number.value, form.phone_number.inputmask.unmaskedvalue());
            showAlert(
                'Confirmar Alteração',
                'Deseja realmente salvar as novas informações do hotel?',
                'question'
            ).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            });
        });
    }
});
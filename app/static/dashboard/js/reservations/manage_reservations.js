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
    const requestBtn = document.querySelectorAll(".btn-update-request");

    updateBtn.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.href;
            const title = this.dataset.text;
            showAlert(title, "Essa ação é irreversível.", "question")
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
            const title = this.dataset.text;
            showAlert(title, "Essa ação é irreversível.", "warning")
            .then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
    requestBtn.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();

            const url = this.href;
            const title = this.dataset.text;
            showAlert(title, "Essa ação atualizará a permissão do hóspede solicitar algum serviço.", "question")
            .then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        const response = await fetch(url, {
                            method: 'GET',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                        const data = await response.json();
                        if (data.ok) {
                            showAlert('Sucesso', data.message || 'Reserva atualizada com sucesso.', 'success', true, 2000)
                            .then(() => {
                                location.reload();
                            });
                        } else {
                            showAlert('Erro', data.message || 'Ocorreu um erro ao buscar os detalhes da solicitação.', 'error', true, 2500);
                        }
                    } catch (error) {
                        showAlert('Erro desconhecido', error, 'error')
                    }
                }
            })
        })
    })
});
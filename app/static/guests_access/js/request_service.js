import { showAlert } from '../../dashboard/js/alerts.js';

const form = document.getElementById('serviceRequestForm');
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const serviceDescription = document.getElementById('serviceRequestDescription').value;

    if (!serviceDescription) {
        showAlert('Atenção', 'Por favor, descreva o serviço que deseja solicitar.', 'warning', true, 2500);
        return;
    }

    const form = new FormData();
    form.append('service_description', serviceDescription);
    try {
        const response = await fetch('/guests/request', {
            method: 'POST',
            body: form,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await response.json();
        if (data.ok) {
            showAlert('Sucesso', data.message, 'success', true, 2500)
            .then(() => {
                location.reload();
            });
        } else {
            showAlert('Erro', data.message || 'Ocorreu um erro ao enviar a solicitação.', 'error', true, 2500);
        }
    }
    catch (error) {
        showAlert('Erro desconhecido', error, 'error')
    }
});

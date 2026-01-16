import { showAlert } from '../../dashboard/js/alerts.js';

const requestModal = document.getElementById('solicitacaoServico');
requestModal.addEventListener('show.bs.modal', async (event) => {
    const button = event.relatedTarget;
    const requestId = button.getAttribute('data-request');

    try {
        const response = await fetch(`/guests/load_request/${requestId}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await response.json();
        if (data.ok) {
            document.getElementById('requestedServiceDescription').value = data.service_request.request;
        } else {
            showAlert('Erro', data.message || 'Ocorreu um erro ao buscar os detalhes da solicitação.', 'error', true, 2500);
        }
    } catch (error) {
        showAlert('Erro desconhecido', error, 'error')
    }
});
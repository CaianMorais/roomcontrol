import { showAlert } from '../alerts.js';

document.querySelectorAll('.service-status-btn').forEach(button => {
    button.addEventListener('click', async function (e) {
        e.preventDefault();

        const newStatus = this.dataset.status;
        const text = this.dataset.text;

        showAlert('Tem certeza?',
            `Você quer ${text}.`,
            'question'
        ).then(async (response) => {
            if (!response.isConfirmed) return;

            try {
                const res = await fetch('/dashboard_services/update_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ status: newStatus })
                })

                const data = await res.json();

                if (data.ok) {
                    await showAlert("Atualizado!",
                        data.message || 'O status do pedido foi atualizado com sucesso.',
                        'success',
                        true, 2000
                    );
                    window.location.reload();
                } else {
                    showAlert('Erro!',
                        data.message || 'Não foi possível atualizar o pedido.',
                        'error',
                        true, 2000
                    );
                }
            } catch (error) {
                console.log(error);
                await showAlert('Erro!',
                    'Houve um erro ao atualizar o pedido. Por favor, tente novamente.',
                    'error',
                    true, 2000
                );
            }
        })
    });
});
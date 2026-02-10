import { showAlert } from '../alerts.js';

const buttons = document.querySelectorAll(".update_api_key");

buttons.forEach((button) => {
    button.addEventListener("click", function() {
        const keyId = this.dataset.id;
        const keyName = this.dataset.name;
        const keyStatus = this.dataset.status;

        let alertResult;

        if (keyStatus === "active") {
            alertResult = showAlert(
                `Desativar a chave ${keyName}?`,
                'Essa chave não estará mais permitida a fazer consultas na API!',
                'question'
            );
        }
        else {
            alertResult = showAlert(
                `Ativar a chave ${keyName}?`,
                'Essa chave vai poder fazer consultas na API!',
                'question'
            )
        }
        alertResult.then((result) => {
            if (result.isConfirmed) {
                window.location.href = `/dashboard_api_keys/update/${keyId}`;
            }
        });
    });
});

const btnNewKey = document.getElementById("new_api_key");

btnNewKey.addEventListener("click", async () => {
    const { value: keyName } = await Swal.fire({
        title: "Criar nova API Key",
        text: "Defina um nome para identificar esta chave.",
        input: "text",
        inputPlaceholder: "Ex.: Integração PowerBI",
        showCancelButton: true,
        confirmButtonText: "Gerar chave",
        cancelButtonText: "Cancelar",
        inputValidator: (value) => {
            if (!value) {
                return "O nome da chave é obrigatório.";
            }
        }
    });

    if (!keyName) return;

    Swal.fire({
        title: "Gerando chave...",
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
    });

    try {
        const response = await fetch("/dashboard_api_keys/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: keyName })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || "Erro ao gerar API Key");
        }

        await Swal.fire({
            title: "API Key criada",
            html: `
                <p><strong>Copie esta chave agora.</strong></p>
                <p>Ela <u>não poderá ser exibida novamente</u>.</p>
                <pre style="user-select: all; word-break: break-all; background:#f4f4f4; padding:10px; border-radius:6px;">${data.api_key}</pre>
            `,
            icon: "success",
            confirmButtonText: "Entendi"
        })

    } catch (error) {
        Swal.fire({
            title: "Erro",
            text: error.message,
            icon: "error"
        });
    }
});
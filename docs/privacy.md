# Privacidade, custos e direitos

O repositório distribui código, instruções e templates vazios. Ele não fornece chaves, vozes, avatares, mídias de produção ou identidade editorial de outro canal.

## Credenciais

- Configure suas próprias chaves e IDs no `.env` do projeto instalado.
- Não cole segredos na conversa, em issues, pull requests ou páginas de aprovação.
- Os scripts leem somente o `.env` explicitamente indicado, sem buscar credenciais em outros projetos.
- Não persista chaves em payloads, manifestos, HTML ou logs.
- O `.env.example` compartilhado deve permanecer com todos os valores vazios.

O `.gitignore` ajuda a evitar inclusão acidental, mas não remove arquivos já versionados nem protege um ZIP feito da pasta inteira.

Antes de compartilhar mudanças, revise os arquivos staged e o histórico do Git. Os testes de privacidade verificam templates vazios, arquivos indevidos e formatos comuns de segredos; não substituem uma auditoria de todas as credenciais reais.

Se uma chave for exposta, revogue-a no provedor e crie outra. Apagar o arquivo do commit atual não a remove do histórico nem de cópias já baixadas.

## O que compartilhar

Compartilhe o repositório limpo ou uma cópia obtida dele. Não compartilhe a pasta de produção configurada sem uma revisão separada.

Mantenha fora do pacote:

- `.env` e qualquer configuração preenchida com credenciais.
- Ambientes Python, caches e logs.
- Materiais particulares de `inputs/` e `private-references/`.
- Jobs, aprovações, áudios, avatares e vídeos produzidos.
- Contextos editoriais privados e arquivos de outros canais.

O template do canal não é um backup do seu projeto. Ele é o ponto de partida para outra pessoa configurar o próprio canal.

## Uso dos serviços

Áudio, animação e transcrição podem consumir créditos nas suas contas. Antes de produzir, o agente deve informar a configuração e estimar o custo conforme as condições disponíveis para você.

Os comandos de geração exigem `--allow-paid`, que só deve ser usado após autorização humana. Instalação, diagnóstico local, dry-runs e testes não fazem chamadas pagas. Não há retry pago automático: um resultado incerto exige conferir arquivos e IDs externos antes de autorizar outra tentativa.

## Voz, avatar e mídias

Use uma voz própria ou licenciada e um avatar autorizado. Referências de terceiros podem orientar características, mas não são permissão para clonar uma pessoa. Criação e clonagem não fazem parte do onboarding automático.

Mídia publicada por uma fonte oficial não é, por isso, liberada para reutilização. Registre origem, autoria, licença, alterações e pendências. Crédito não substitui permissão quando ela for necessária.

A aprovação estética de uma mídia e a autorização de publicação são decisões distintas. O fluxo não contorna DRM, acesso privado ou restrições de aquisição.

Os serviços, dependências e mídias mantêm suas próprias licenças e condições de uso. O kit não transfere assinaturas, créditos nem direitos sobre conteúdo de terceiros.

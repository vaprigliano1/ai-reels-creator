# Crie seu primeiro Reel

O repositório contém as ferramentas. O projeto instalado contém o contexto, a configuração e os vídeos do seu canal. Mantenha essas duas pastas separadas para atualizar e compartilhar o código sem compartilhar dados pessoais.

## 1. Prepare suas contas

Tenha à mão:

- **ElevenLabs:** conta, chave de API, créditos, uma voz própria ou licenciada e o ID dessa voz.
- **HeyGen:** conta, chave de API, créditos, um avatar autorizado e o ID compatível com o motor escolhido.
- **Ambiente local:** Python 3.11+, FFmpeg, FFprobe e um agente com pesquisa na web e acesso ao terminal.

O áudio será gerado na ElevenLabs. A HeyGen recebe esse áudio para animar o avatar, não para criar outra voz. Nenhuma voz ou avatar é criado ou clonado automaticamente durante a instalação.

O agente deve verificar os modelos e o acesso de API da sua conta antes de produzir. Não confunda o nome comercial de um modelo com o `model_id` usado pela API.

## 2. Instale o projeto

No terminal:

```sh
git clone https://github.com/vaprigliano1/ai-reels-creator.git
cd ai-reels-creator
python3 install.py --workspace ../meu-canal --install-skill --setup-python
```

No Windows, use `py -3` no lugar de `python3`, caso seja o comando disponível.

O instalador:

- Copia o template para uma pasta nova ou vazia.
- Cria um `.env` vazio com permissão restrita onde o sistema suporta esse controle.
- Inclui a skill local em `.agent/skills/channel-video/`.
- Com `--install-skill`, também instala `channel-video` no diretório de skills do Codex.
- Com `--setup-python`, cria uma `.venv` e instala as dependências Python do projeto.

Não há chamadas às APIs durante a instalação. FFmpeg e FFprobe precisam ser instalados separadamente pelo método adequado ao seu sistema.

Se a skill global já existir, o instalador para sem sobrescrevê-la. Você pode omitir `--install-skill` e pedir ao agente que leia a cópia local. Outros agentes também podem usar `AGENTS.md` e a skill local, sem a instalação global do Codex.

## 3. Defina o canal com o agente

Abra a pasta `meu-canal` e envie:

> Leia AGENTS.md e use a skill channel-video. Faça o onboarding do meu canal. Se eu não tiver um contexto editorial, me faça as perguntas necessárias e escreva um para minha aprovação. Não gere mídia paga ainda.

O agente deve entender o público, os assuntos, o idioma, a personalidade da voz, as referências visuais e as restrições. Ele propõe o contexto e as preferências; você confirma antes de começar.

| Arquivo | Para que serve |
| --- | --- |
| `channel_context.md` | Posicionamento, linguagem, referências e direção editorial. |
| `channel_profile.json` | Preferências estruturadas: idioma, duração, layout e aprovações. |
| `.env` | Suas chaves, IDs de voz/avatar e modelos configurados. |

O perfil começa com `approved: false`. Preencher campos não equivale a aprovar o contexto.

## 4. Configure as credenciais localmente

Peça ao agente para abrir o `.env` e preencha você mesmo:

```dotenv
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=
ELEVENLABS_STT_MODEL_ID=
HEYGEN_API_KEY=
HEYGEN_AVATAR_ID=
HEYGEN_ENGINE=
HEYGEN_REFERENCE_LOOK_ID=
CAPTION_FONT_PATH=
```

Os dois últimos campos são opcionais. O ID de aparência só deve ser usado se for compatível com o motor/endpoint configurado. A fonte de legenda deve estar instalada localmente e permitida para uso.

Não cole os valores na conversa nem envie o `.env` ao GitHub. O agente deve usar somente a configuração deste projeto.

Na pasta do canal, confira a preparação local:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/doctor.py --workspace .
```

No Windows, troque `.venv/bin/python` por `.venv\Scripts\python.exe`. Esse diagnóstico não chama APIs nem imprime valores de credenciais. Ele confirma dependências e campos preenchidos; não comprova acesso remoto ou validade das chaves.

## 5. Peça o primeiro vídeo

Você pode começar com:

> Crie um Reel sobre a história deste negócio. Use o contexto do canal, pesquise fontes confiáveis e apresente o roteiro antes de gerar o áudio.

Ou adaptar algo que já tem:

> Transforme este dossiê em um Reel. Pesquise apenas as lacunas importantes e adapte a duração ao material, sem repetir informação para preencher tempo.

Primeiro, aprove o roteiro e um teste curto de voz. Depois, autorize o áudio completo e o lip-sync. O agente apresentará uma página para decidir quais mídias usar e, por fim, um preview para revisão.

Para detalhes das etapas, veja [como funciona](workflow.md). Para o uso dos scripts, veja os [comandos técnicos](../skills/channel-video/references/operations.md).

## Se algo não funcionar

- **Pasta de destino ocupada:** escolha uma pasta nova; a instalação não substitui um projeto existente.
- **Skill já instalada:** use a cópia local ou revise a versão existente antes de trocá-la.
- **Diagnóstico incompleto:** confira dependências, contexto aprovado, idioma e campos do `.env`.
- **Erro de API:** verifique permissões, créditos, modelo e IDs da própria conta. Antes de tentar uma geração novamente, confira se a primeira tentativa já criou um arquivo ou ID externo.
- **Avatar sem transparência ou recorte inadequado:** revise o formato de saída e o enquadramento antes de compor o vídeo.

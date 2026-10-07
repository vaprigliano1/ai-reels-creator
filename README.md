# AI Reels Creator

Kit neutro para um agente produzir vídeos narrados com voz ElevenLabs, avatar HeyGen, mídias de apoio, legendas e MP4 final. Aceita qualquer tema, pedido avulso, pesquisa, texto publicado ou roteiro pronto. Não contém canal predefinido, credenciais, IDs, vozes, avatares ou mídias de outra pessoa.

## O que você precisa

- Agente com leitura/escrita de arquivos, terminal e ferramenta de pesquisa na web. Codex é a instalação descrita abaixo; outros agentes podem ler `AGENTS.md` e `SKILL.md` diretamente.
- **Sua conta HeyGen**, chave de API e acesso/créditos para o motor de animação escolhido. A assinatura do aplicativo pode não incluir o acesso de API necessário; confira na própria conta.
- **Seu avatar na HeyGen**, autorizado para uso, e seu `HEYGEN_AVATAR_ID` ou ID da aparência compatível com o endpoint usado. Confirme qual tipo de ID a sua conta expõe.
- **Sua conta ElevenLabs**, chave de API com acesso a TTS e transcrição, e créditos disponíveis.
- **Sua voz na ElevenLabs**, própria ou licenciada, e seu `ELEVENLABS_VOICE_ID`. Não é um ID de voz da HeyGen.
- Python 3.11 ou superior, FFmpeg e FFprobe no PATH; acesso à internet e espaço para os vídeos.

Nenhuma voz ou avatar é criado/clonado automaticamente. Referências de terceiros servem para discutir características, não como permissão para clonagem. O áudio é gerado na ElevenLabs e enviado à HeyGen somente para animar/sincronizar.

## Instalação

Clone este repositório ou baixe e descompacte o ZIP. No terminal da pasta do kit:

```sh
python3 install.py --workspace /caminho/para/meu-canal --install-skill --setup-python
```

Escolha uma pasta nova/vazia. O instalador cria o projeto, a configuração vazia, o ambiente Python e instala `channel-video` no diretório de skills do Codex. Se a skill já existir, ele para em vez de sobrescrevê-la. Para outro agente, omita `--install-skill`: o projeto já contém a skill em `.agent/skills/channel-video/`.

Instale FFmpeg/FFprobe pelo método apropriado ao seu sistema. O instalador não modifica configurações globais nem instala esses binários por conta própria.

Abra a pasta do novo projeto no agente e envie:

> Leia AGENTS.md e use a skill channel-video. Faça o onboarding do meu canal antes de gerar qualquer mídia paga. Se eu ainda não tiver um contexto, me entreviste e escreva um para minha aprovação.

O agente perguntará sobre público, assuntos, idioma, personalidade da voz, referências visuais, duração e restrições. Ele produzirá `channel_context.md` e `channel_profile.json` e pedirá confirmação. Não é necessário preencher manualmente um documento extenso.

Depois, preencha **seu próprio** `.env` local com suas chaves e IDs. Não cole segredos na conversa. Todos os campos sensíveis do pacote vêm vazios. O agente pode abrir o arquivo para você, mas não deve mostrar seus valores.

## Primeiro vídeo e rotina

Exemplo de pedido: “Crie um vídeo sobre este tema, usando o contexto do meu canal”. Também é possível anexar um dossiê ou pedir a adaptação de um texto existente.

O agente pesquisa na medida necessária, escreve o roteiro, prepara falas e legenda do post, faz teste curto de voz e pede aprovação. Depois gera o áudio completo, pede aprovação de novo, anima seu avatar, transcreve o áudio, pesquisa mídias por trecho e apresenta uma página de aprovação. Só após as decisões baixa os arquivos finais e monta o vídeo.

Você recebe `preview.mp4` para revisar. A versão consolidada fica em `videos/<tema>/video final/final_<pauta>.mp4`. Essa pasta contém somente MP4 finais; créditos, legenda do post, plano e histórico ficam fora dela.

Os scripts são ferramentas do agente, não um botão que toma todas as decisões editoriais. Pesquisa, escrita, escolha de enquadramento e avaliação visual ainda dependem do agente e da sua aprovação. O renderizador incluído cobre montagem vertical com imagens/vídeos, avatar, overlays opcionais e legendas, sem exigir outro repositório de edição.

## Configuração e custos

As chaves e IDs estão em `.env`. Idioma e estilo estão em `channel_profile.json`. Modelo de voz e motor HeyGen são escolhas do novo proprietário: não há um modelo privado ou ID herdado. O agente deve conferir disponibilidade, capacidades e limites na conta/documentação antes de sugerir a configuração; não presumir que o nome comercial de um modelo coincide com o seu `model_id`.

Geração de áudio, animação e transcrição podem consumir créditos. Os helpers de geração exigem `--allow-paid`; isso só deve ser usado após autorização humana. Não existe retry pago automático. O kit não contém créditos, assinaturas ou licenças de mídia. Uma aprovação estética não substitui autorização de uso de terceiros.

O token/API de Instagram e agendamento de posts **não fazem parte deste kit**. Criar ou aprovar um vídeo não autoriza sua publicação.

## Verificação

Na pasta do novo projeto, usando o Python do ambiente `.venv`:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/doctor.py --workspace .
.venv/bin/python .agent/skills/channel-video/scripts/test_kit.py
```

No Windows, use `.venv\Scripts\python.exe` no lugar de `.venv/bin/python`.

`doctor.py` não chama APIs nem imprime chaves. Os testes usam arquivos sintéticos e simulações, sem cobrança. A integração real deve ser validada com uma amostra curta **na sua própria conta**, após autorização.

Para renderizar, o agente usa `edit/render_plan.json`, com fontes aprovadas e tempos medidos. Leia `skills/channel-video/references/operations.md` para os comandos e `render-plan.md` para o contrato.

## Privacidade

- Compartilhe o ZIP original, não a pasta de trabalho depois de configurá-la.
- Não compartilhe `.env`, `.venv`, jobs, logs, áudios, avatares ou referências pessoais por acidente.
- `.gitignore` exclui segredos e arquivos de produção, mas isso não protege um ZIP feito manualmente da pasta inteira.
- Revogue qualquer chave exposta e crie outra; não basta apagar a mensagem ou o arquivo.

Os arquivos próprios deste kit podem ser copiados e adaptados. Dependências de terceiros preservam suas licenças; FFmpeg, bibliotecas, plataformas e mídias não são relicenciados pelo kit.

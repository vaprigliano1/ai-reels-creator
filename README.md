# AI Reels Creator

Transforme uma pauta em um Reel com a sua voz, o seu avatar e o estilo do seu canal.

Um fluxo de produção para agentes como o Codex: pesquisa, roteiro, áudio ElevenLabs, lip-sync HeyGen, imagens e vídeos reais, legendas e entrega em MP4. Você aprova as decisões importantes; o agente organiza e executa a produção.

[Começar](docs/getting-started.md) · [Como funciona](docs/workflow.md) · [Privacidade e custos](docs/privacy.md)

## Do tema ao vídeo

- **Conteúdo com contexto.** Comece com uma ideia, pesquisa, carrossel ou roteiro pronto. O agente adapta a abordagem ao seu público.
- **Sua voz e seu avatar.** ElevenLabs gera o áudio; HeyGen anima o avatar com o mesmo arquivo aprovado.
- **Mídias alinhadas à fala.** Imagens, vídeos, retratos e logos entram nos trechos relevantes, com fontes e créditos registrados.
- **Revisão antes da entrega.** Aprove o áudio, as mídias e o preview. O fluxo não publica nem agenda posts.
- **Um projeto organizado.** Roteiro, áudio, mídias e histórico ficam separados; a pasta de entrega contém apenas o MP4 final.

## O que você precisa

- Um agente com acesso a arquivos, terminal e pesquisa na web. A instalação abaixo inclui uma skill para Codex.
- Uma conta **ElevenLabs**, chave de API, créditos e uma voz própria ou licenciada.
- Uma conta **HeyGen**, chave de API, créditos e um avatar autorizado para uso.
- Python **3.11+**, FFmpeg e FFprobe disponíveis no terminal.

Confirme o acesso de API e os modelos disponíveis nas suas contas. O repositório não inclui assinaturas, créditos, vozes, avatares nem credenciais.

## Comece aqui

Clone o repositório e instale em uma pasta nova ou vazia:

```sh
git clone https://github.com/vaprigliano1/ai-reels-creator.git
cd ai-reels-creator
python3 install.py --workspace ../meu-canal --install-skill --setup-python
```

Abra `meu-canal` no Codex e envie:

> Leia AGENTS.md e use a skill channel-video. Me ajude a definir o contexto do meu canal, apresente-o para aprovação e confira a configuração antes de gerar mídia paga.

O agente conduz uma conversa sobre público, temas, linguagem e estética. Depois, você preenche suas chaves e IDs no `.env` local — nunca na conversa.

Com o contexto aprovado, peça o primeiro vídeo:

> Crie um Reel sobre este tema, seguindo o contexto do meu canal. Apresente o roteiro e um teste curto de voz antes da produção completa.

Para Windows, outros agentes e instalação sem skill global, consulte o [guia de início](docs/getting-started.md).

## Fluxo de produção

Pauta → pesquisa → roteiro → áudio aprovado → avatar → mídias aprovadas → montagem → preview → MP4 final.

A pesquisa, a escrita e a direção visual são conduzidas pelo agente. Os scripts cuidam das etapas técnicas e do registro dos arquivos. Não é um aplicativo com frontend nem um comando que decide tudo sozinho.

A entrega fica no projeto do seu canal:

```text
videos/<tema>/
├── reel_<pauta>.md          Roteiro, legenda do post e fontes
├── falas_<pauta>.md         Texto preparado para a voz
├── video_<pauta>/           Áudio, avatar, mídias, preview e histórico
└── video final/
    └── final_<pauta>.mp4    Versão consolidada
```

Veja os [passos, aprovações e entregáveis](docs/workflow.md).

## Dentro do repositório

- [`templates/channel/`](templates/channel/) — projeto inicial, perfil editorial e configuração vazia.
- [`skills/channel-video/`](skills/channel-video/) — instruções do agente e ferramentas de produção.
- [`docs/`](docs/) — instalação, fluxo e cuidados com privacidade.
- [`tests/`](tests/) — testes locais, sem credenciais nem chamadas pagas.

## Desenvolvimento e verificação

Na pasta deste repositório:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

No Windows, use `.venv\Scripts\python.exe`. Instale FFmpeg e FFprobe para executar também o teste de montagem. A integração com as APIs deve ser validada com um teste curto autorizado na conta de quem vai produzir.

## Privacidade, custos e direitos

Cada canal começa sem identidade ou credenciais herdadas. Gerações pagas exigem autorização; não há repetição automática de uma tentativa incerta. Uma mídia pública não é necessariamente licenciada, e aprovar o vídeo não autoriza publicá-lo.

Leia os [cuidados de configuração e compartilhamento](docs/privacy.md) antes de produzir. Os serviços, bibliotecas e mídias mantêm suas próprias condições de uso.

# Comandos do agente

Exemplos relativos à raiz do projeto instalado. Usar o Python de `.venv`; no Windows, trocar por `.venv\Scripts\python.exe`. Não executar campos preenchidos em exemplos como se fossem arquivos reais.

1. Criar `videos/<tema>/reel_<pauta>.md` e `falas_<pauta>.md`, depois:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/init_job.py videos/tema/reel_pauta.md
.venv/bin/python .agent/skills/channel-video/scripts/doctor.py --workspace .
```

2. Conferir modelo, idioma, caracteres e payload sem cobrança:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/elevenlabs_audio.py --env .env --job-dir videos/tema/video_pauta --script-file videos/tema/falas_pauta.md --smoke-test --dry-run
```

3. Somente após autorização, usar o mesmo comando com `--allow-paid` no lugar de `--dry-run`. Mostrar arquivo curto. Após sua aprovação e autorização da fala inteira, remover `--smoke-test` e gerar a fala completa. Escolher limites/settings válidos para o modelo do proprietário; defaults não garantem compatibilidade com toda conta.

4. Depois que o proprietário ouvir e aprovar o MP3 exato:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/approve_audio.py --job-dir videos/tema/video_pauta --audio-file videos/tema/video_pauta/audio/arquivo_aprovado.mp3
.venv/bin/python .agent/skills/channel-video/scripts/heygen_video.py --env .env --job-dir videos/tema/video_pauta --audio-file videos/tema/video_pauta/audio/arquivo_aprovado.mp3 --dry-run
```

Autorizar animação e trocar `--dry-run` por `--allow-paid`. O adapter usa HeyGen `/v3/assets` e `/v3/videos`, `audio_asset_id` e motor configurado; confirmar disponibilidade para a conta. Polling pode ser retomado sem nova geração se o ID externo estiver registrado. Não garantir que o header de idempotência evita cobrança em todos os endpoints: os arquivos de tentativa e IDs locais são parte da proteção.

5. Autorizar transcrição e executar:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/transcribe.py --env .env --job-dir videos/tema/video_pauta --audio-file videos/tema/video_pauta/audio/arquivo_aprovado.mp3 --allow-paid
```

O adapter usa ElevenLabs `/v1/text-to-speech/{voice_id}` e `/v1/speech-to-text`; IDs de modelo vêm do `.env`, sem tradução automática de nomes comerciais. Não há chamadas pagas na instalação nem nos testes. Documentação atual do fornecedor deve prevalecer quando uma API mudar; adaptar explicitamente e fazer teste curto em vez de gastar em produção completa.

6. Gerar/revisar manifesto e previews locais. A página pode ser aberta pelo agente ou servida somente no loopback:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/contact_sheet.py videos/tema/video_pauta/media/asset_manifest.json -o videos/tema/video_pauta/approvals/media.html
.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory videos/tema/video_pauta
```

O servidor é local e iniciado em uma pasta sem `.env`. Abrir `http://127.0.0.1:8765/approvals/media.html`, aprovar/rejeitar e exportar. Em seguida:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/import_approvals.py videos/tema/video_pauta/media/asset_manifest.json /caminho/para/media_approval.json
.venv/bin/python .agent/skills/channel-video/scripts/download_media.py --job-dir videos/tema/video_pauta --manifest videos/tema/video_pauta/media/asset_manifest.json
```

O download requer URL direta HTTPS verificada. Para outra aquisição legítima, usar ferramentas autorizadas do ambiente e registrar o arquivo/hash/proveniência no manifesto; não usar bypass de acesso. O board não confere licença nem transforma pendência em aprovação.

7. Preparar render_plan.json conforme contrato e executar:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/render.py --env .env --job-dir videos/tema/video_pauta --plan videos/tema/video_pauta/edit/render_plan.json --dry-run
.venv/bin/python .agent/skills/channel-video/scripts/render.py --env .env --job-dir videos/tema/video_pauta --plan videos/tema/video_pauta/edit/render_plan.json
.venv/bin/python .agent/skills/channel-video/scripts/qa.py --job-dir videos/tema/video_pauta --plan videos/tema/video_pauta/edit/render_plan.json
```

Inspecionar preview e imagens de QA, ouvir áudio e obter aprovação editorial. Registrar `steps.final_approval = "completed"` no job somente após confirmação. Salvar:

```sh
.venv/bin/python .agent/skills/channel-video/scripts/save_final.py --job videos/tema/video_pauta/job.json --source videos/tema/video_pauta/preview.mp4 --basis approved
```

`--replace` arquiva a entrega anterior, e só se usa após verificar o alvo. Pedido explícito para consolidar a versão atual pode usar `--basis user_requested_consolidation`, sem alterar aprovações/direitos. Não promover um render antigo quando o vigente estiver ausente.

## Estado

`job.json` registra etapas, artefatos, hashes, aprovações e IDs externos não secretos. Cada áudio/preview novo preserva o anterior. Erro incerto de geração não autoriza retry. Antes de usar `--retry-paid`, conferir dashboard/IDs/artefatos e pedir autorização para outra tentativa.

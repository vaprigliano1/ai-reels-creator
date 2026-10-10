---
name: channel-video
description: Produz ou retoma vídeos narrados para um canal configurado pelo proprietário, com pesquisa, roteiro, áudio ElevenLabs, lip-sync HeyGen, mídia de apoio, legendas, aprovação e MP4 final. Use para produção completa ou onboarding, não para publicar posts.
---

# AI Reels Creator

Este método não traz identidade de canal, credenciais, modelos ou pessoas predefinidas. Leia o `AGENTS.md` do projeto. No projeto instalado, os helpers estão em `.agent/skills/channel-video/scripts/`.

## Onboarding obrigatório

Se contexto/perfil ainda não estiverem aprovados, leia `references/onboarding.md` e conduza a conversa antes de gerar mídia paga. Crie o contexto do canal a partir das respostas, proponha preferências configuráveis e peça aprovação. Não inferir aprovação a partir de campos preenchidos. O proprietário precisa de suas próprias contas HeyGen e ElevenLabs, sua voz ElevenLabs e seu avatar HeyGen, com acesso de API e créditos.

Nenhum ID ou segredo deve ser copiado de outro canal, ambiente global ou conversa. O `.env` deve ser o do workspace atual; não há busca automática de credenciais fora dele.

## Fluxo

1. Leia `channel_context.md` e `channel_profile.json`. Identifique pedido avulso, dossiê, texto publicado ou roteiro pronto. Reutilize tema existente ou crie `videos/<tema>/`.
2. Para roteiro novo, leia `references/editorial.md`. Pesquisa aprofundada para pedido raso; pesquisa de lacunas para dossiê denso. O tema não precisa ser viagem, hotel, founder ou negócio. Ajuste a narrativa e a duração ao material, sem repetir fatos para bater um tempo fixo.
3. Salve roteiro, fontes, legenda do post e falas. Se já houver roteiro aprovado, preserve-o. Inicialize `job.json` com `scripts/init_job.py`; confira dependências/configuração com `doctor.py`.
4. Confira o `model_id` real, idioma, limites e suporte a tags na documentação/conta do proprietário. Mantenha tags compatíveis se ele quiser; não pronunciar tags em um modelo incompatível. A API não deve receber um nome de modelo comercial inventado como ID. Faça dry-run e explique caracteres/configuração/custo estimado sem imprimir credenciais.
5. Peça autorização para o teste curto pago e gere com `elevenlabs_audio.py --smoke-test --allow-paid`. Mostre o áudio real, sem alegar ter ouvido o que não ouviu. Aprovação do teste não aprova automaticamente a fala completa.
6. Após autorização, gere a fala inteira e peça aprovação explícita do arquivo. Registre SHA-256 com `approve_audio.py`. Não usar gravação de celular como áudio de produção sem pedido do proprietário.
7. Após autorização do lip-sync, execute `heygen_video.py --allow-paid` com o mesmo MP3 aprovado. HeyGen recebe `audio_asset_id`; não sintetiza o roteiro novamente. Valide transparência, identidade, gestos e recorte do busto.
8. Transcreva a fala aprovada com `transcribe.py --allow-paid`. Os timestamps reais determinam B-roll, overlays e legendas. Verifique nomes, números e idioma; áudio novo exige novo lip-sync.
9. Leia `references/media.md`. Pesquise mídia coerente por trecho, registre proveniência e intervalo exato em `asset_manifest.json`, e gere página de revisão com `contact_sheet.py`. Não baixar arquivos finais antes das decisões. Importe o JSON exportado com `import_approvals.py`, conferindo o hash do manifesto; decisão ausente continua pendente.
10. Baixe fontes diretas aprovadas com `download_media.py` ou ferramentas autorizadas do ambiente. URLs de página não são URLs de vídeo. Não contornar DRM, acesso privado ou termos de uso. Registre créditos, alterações e permissões separadamente.
11. Leia `references/render-plan.md` e `operations.md`. Monte um plano com mídia aprovada, intervalos medidos, avatar e legendas. `render.py` usa FFmpeg e tipografia rasterizada, sem exigir outro editor. Overlays oficiais ou retratos recortados são opcionais e dependem do estilo do canal. Não redesenhar logos nem fabricar fotos documentais.
12. Leia `references/qa.md`, execute `qa.py` e faça inspeção visual real. Checagem técnica não certifica estética, pronúncia, estabilidade ou direitos. Entregue preview para aprovação. Consolide o MP4 vigente em `video final/` com `save_final.py`, sem reencodar e preservando histórico.

## Retomada e segurança

- Leia estados/artefatos antes de executar. Não gerar de novo o que existe e tem hash válido.
- Segredos somente do `.env` explicitamente indicado. Nunca em payloads persistidos, logs, HTML, manifestos ou pacote compartilhável.
- Nenhum retry pago automático. Resultado incerto exige inspeção e autorização nova; IDs externos registrados devem ser usados para retomar polling.
- Não transferir um avatar/voz para outro canal por conveniência. Criação/clonagem exige escopo e direitos próprios, não faz parte do onboarding automático.
- Não alterar o contexto aprovado, trocar o modelo ou cortar roteiro silenciosamente. Pedir decisão quando isso mudar materialmente a produção.
- Capa e legenda podem ser produzidas como artefatos separados quando pedidas; conectar redes sociais, publicar ou agendar exige integração/autorização própria.

Os scripts não substituem pesquisa, direção e validação humana. Os defaults de layout são ajustáveis; as invariantes de áudio aprovado, custeio, proveniência e proteção de segredos não são preferências estéticas.

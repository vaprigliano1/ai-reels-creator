# Como funciona

O AI Reels Creator combina direção editorial pelo agente com ferramentas locais de produção. Você escolhe o tema e aprova o resultado; o agente mantém contexto, arquivos e decisões organizados.

## Entradas

Uma pauta avulsa pede mais pesquisa. Um dossiê denso pede checagem de lacunas. Um carrossel pede adaptação para fala. Um roteiro já aprovado deve ser preservado, a menos que você peça mudanças.

Não há nicho obrigatório nem duração fixa. A história e o contexto do canal determinam o tempo, o tom, o ritmo e a seleção das mídias.

## Etapas e aprovações

| Etapa | Resultado | Sua decisão |
| --- | --- | --- |
| Contexto | Público, temas, linguagem e estética do canal. | Aprovar o perfil editorial. |
| Pesquisa e roteiro | Fatos, fontes, falas e legenda do post. | Aprovar a abordagem e o roteiro. |
| Teste de voz | Amostra curta com a voz e o modelo escolhidos. | Autorizar o teste pago e ouvir o resultado. |
| Áudio completo | Fala final com hash de identificação. | Autorizar a geração e aprovar o arquivo exato. |
| Avatar | Lip-sync HeyGen usando o áudio aprovado. | Autorizar a animação. |
| Mídias | Imagens e vídeos associados aos trechos da fala. | Aprovar ou rejeitar cada seleção. |
| Montagem | Background, avatar, overlays e legendas sincronizados. | Revisar o preview. |
| Entrega | MP4 consolidado na pasta `video final/`. | Aprovar a versão final. |

Uma aprovação não autoriza automaticamente a próxima etapa paga ou a publicação. Decisões de mídia ausentes continuam pendentes.

## Áudio como fonte de verdade

ElevenLabs gera a voz; HeyGen recebe o mesmo arquivo para animar o avatar. O hash do áudio aprovado acompanha a transcrição e a montagem. Se a fala mudar, é necessário gerar o lip-sync correspondente — não apenas substituir o som de um avatar antigo.

Os timestamps da fala determinam os cortes, os overlays e as legendas. Tags expressivas só devem ser usadas quando o modelo configurado as suportar.

## Direção visual

O agente busca mídia coerente com o assunto e o estilo do canal, inspeciona os trechos e apresenta as opções para revisão. Fotos recebem movimento suave; vídeos preservam assunto e escala; logos e retratos podem entrar como overlays quando fizerem sentido.

A montagem evita repetição de backgrounds, imagens minúsculas, blur excessivo e flashes de cenas anteriores. O enquadramento deve preservar o assunto, especialmente em vídeos horizontais adaptados ao formato vertical.

O renderizador incluído usa FFmpeg. Não depende de outro repositório de edição. Recortes de pessoas, seleção de intervalos, adequação estética e direitos de uso ainda precisam da avaliação do agente e do proprietário.

## Arquivos do seu canal

```text
meu-canal/
├── AGENTS.md
├── channel_context.md
├── channel_profile.json
├── .env                         Credenciais locais; não compartilhar
├── .agent/skills/channel-video/ Instruções e ferramentas locais
├── inputs/                      Materiais que você fornece
├── private-references/          Referências particulares
└── videos/<tema>/
    ├── reel_<pauta>.md
    ├── falas_<pauta>.md
    ├── video_<pauta>/
    │   ├── job.json
    │   ├── audio/
    │   ├── heygen/
    │   ├── transcripts/
    │   ├── media/
    │   ├── approvals/
    │   ├── edit/
    │   └── preview.mp4
    └── video final/
        └── final_<pauta>.mp4
```

`job.json` registra estados, aprovações, hashes e referências aos artefatos. Ao retomar um vídeo, o agente deve conferir esse registro antes de gerar novamente algo que já existe.

## Revisão e entrega

A checagem técnica decodifica o vídeo e extrai frames próximos aos cortes. Ela não substitui assistir ao preview, ouvir nomes e pronúncias, conferir estabilidade, recortes, contraste e sincronização.

A entrega copia o MP4 validado sem reencodar e verifica o SHA-256. A pasta `video final/` contém somente a versão vigente de cada Reel. Previews, áudios, documentos e versões anteriores ficam fora dela.

O fluxo não inclui conexão com Instagram, publicação ou agendamento. Esses passos exigem uma integração e autorização separadas.

## Referências técnicas

- [Comandos de produção](../skills/channel-video/references/operations.md)
- [Contrato de composição](../skills/channel-video/references/render-plan.md)
- [Seleção e aprovação de mídias](../skills/channel-video/references/media.md)
- [Checklist de QA](../skills/channel-video/references/qa.md)

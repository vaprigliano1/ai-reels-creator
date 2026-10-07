# Primeira conversa

Agrupe perguntas em blocos pequenos e aproveite respostas já fornecidas. Não iniciar com um formulário de dezenas de campos.

1. Qual é o nome/objetivo do canal e para quem ele fala? Quais temas pretende cobrir?
2. Qual idioma e variação regional? Tom, ritmo e termos que devem ser evitados? Há referências públicas para discutir características, sem copiar pessoas?
3. Que estética ele quer: informativa, documental, humor, educação, esporte, premium, outra? Links/exemplos de vídeos e o que gosta/não gosta em cada um.
4. Duração desejada, presença/tamanho do avatar, legendas, proporção de foto/vídeo, música e overlays. Se não souber, proponha um teste curto de layout e deixe claro que é uma sugestão.
5. Fontes e licenças disponíveis, restrições de conteúdo, créditos, aprovações e destinos de publicação.

Escreva `channel_context.md` com posicionamento, público, temas, voz editorial, estética, exemplos, anti-exemplos e restrições. Atualize o perfil estruturado correspondente. Apresente ambos, peça confirmação e só então marque `approved: true`. O nome do canal não é título fixo de todos os vídeos.

Explique quatro pré-requisitos de produção: conta HeyGen, conta ElevenLabs, voz ElevenLabs e avatar HeyGen. São do novo proprietário. Chaves, IDs e modelo escolhido ficam no `.env` local; preferências de conteúdo no perfil. `HEYGEN_REFERENCE_LOOK_ID` é opcional e só se usa quando o motor/endpoint o aceitar. Não confundir voz ElevenLabs com voz HeyGen nem ID de avatar com ID de qualquer outro asset.

Depois de preencher, rode doctor local. Validação real da conta deve começar por consultas read-only e amostra curta autorizada; não gerar vídeo completo para descobrir configuração errada. Não prometer API, transparência ou modelo disponível em qualquer plano sem verificar.

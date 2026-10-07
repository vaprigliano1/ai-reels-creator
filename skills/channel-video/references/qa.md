# QA e entrega

Rodar `qa.py` verifica estrutura, codecs, duração, decodificação e fronteiras registradas no plano. É uma verificação técnica básica, não certificação de qualidade editorial.

Inspeção do agente/humano:

- Ouvir take real: naturalidade, idioma, estrangeirismos, nomes, números e pausas.
- Conferir sincronização labial e que o avatar corresponde à aparência escolhida.
- Validar alpha; nenhum fundo preto, borda recortada errada, mão perdida ou padding sob o busto. Tamanho/posição estáveis.
- Inspecionar abertura, todos os overlays, fotos, trechos de vídeo e pelo menos três frames antes/depois de cada corte. Nenhum flash, frame órfão, retorno de cena anterior ou jitter de crop.
- Fotos em movimento suave, rosto e assunto completos; imagens e vídeos nítidos na escala final. Overlays com contraste em todo o intervalo.
- Legendas sincronizadas, legíveis, discretas conforme o contexto e sem cobrir rosto/assunto; aplicar por último.
- Sem mídia repetida inadvertidamente, sem material não aprovado, sem fontes inventadas.
- Créditos referentes aos arquivos usados e pendências de licença explicitadas.
- Áudio sem clipping, silêncio acidental ou diferença de duração; nenhuma aceleração global para encaixar um take em edição antiga.

Mostrar preview e pedir aprovação. Se houver correção, preservar histórico e executar apenas etapas afetadas. Ao consolidar, copiar sem reencodar, verificar hash e guardar somente final vigente em `video final/`. Esse passo não publica nem aprova direitos.

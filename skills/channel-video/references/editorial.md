# Pesquisa e escrita para qualquer tema

- Defina uma pergunta narrativa ou tensão clara e uma promessa honesta nos primeiros segundos. Não impor arco de founder se o assunto não tiver founder.
- Extraia fatos relevantes do material fornecido. Investigue lacunas, cronologia, nomes, dados e controvérsias em fontes primárias quando possível. Diferencie fato, depoimento e interpretação.
- Escreva falado no idioma do canal: específico, conversacional, sem entonação forçada por excesso de tags. Evite adjetivos vazios e enumerações sem propósito.
- Se houver pouca informação interessante, proponha duração menor. Não inventar virada, motivação pessoal, números, benefícios médicos/financeiros ou cenas históricas.
- Alinhe cada trecho a uma mídia ou recurso visual factualmente correto. Foto atual não prova cena histórica. Pessoas e marcas mencionadas devem ser identificadas corretamente.
- Resolva a pergunta de abertura e termine com conclusão/CTA adequados ao público, sem fórmula obrigatória.

## Arquivos

`reel_<pauta>.md`: objetivo, hook, roteiro por beats, direção visual, legenda do post, fontes, limites/pendências e checklist.

`falas_<pauta>.md` deve conter exatamente um bloco:

```markdown
## Roteiro tagueado
\`\`\`text
Texto final da fala. Tags apenas se o modelo as suportar.
\`\`\`
```

Ao criar o arquivo real, use cercas Markdown normais, sem as barras de escape acima. Alternativamente o helper aceita `.txt` com apenas o texto falado. Não mandar à TTS notas, fontes, marcações de segundos ou instruções de edição.

Modelos e tags: conferir documentação atual antes de escolher; manter o texto tagueado aprovado quando compatível. Ajustar língua, pronúncia de nomes/estrangeirismos e representação de números para a voz escolhida, sem uma preferência herdada. Uma amostra curta permite avaliar isso.

Legenda do post: primeira linha clara, complemento útil do vídeo, atribuições/ressalvas necessárias e créditos de mídias efetivamente usadas. Não incluir nomes de fontes só por terem aparecido na pesquisa. Guardar notas internas fora do texto publicável. Conferir limite da plataforma antes de entregar para uso nela.

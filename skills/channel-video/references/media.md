# Mídias e aprovação

Use fontes permitidas pelo contexto do novo canal. Fontes oficiais e autoria identificada são boas opções, mas disponibilização pública não é licença. Evite compilações sem proveniência, cenas factualmente erradas e low-res que não aguenta o crop. Nunca baixar/compor material pessoal de outro workspace por fallback.

Trocas de 3 a 6 segundos são um ponto de partida, não quota. Ajuste ao ritmo da fala. Misture planos e distâncias, evite repetição e não interrompa uma ação antes de ser compreendida. Nas fotos, prefira pan lateral suave. Em vídeo, preserve assunto e escala; blur moderado quando necessário, não uma janela minúscula.

Fontes com títulos, legendas, HUD ou lower thirds devem ser avaliadas conforme as restrições do canal. Prefira intervalos limpos para não competir com as legendas finais. Logos oficiais e retratos podem ser overlays editoriais separados com contraste e alpha verdadeiro; não baixar versões pixeladas nem gerar aproximações de marcas.

## Manifesto

```json
{
  "version": 1,
  "audio_sha256": "hash do take aprovado",
  "slots": [
    {
      "id": "S01",
      "start": 0.0,
      "end": 4.0,
      "narration": "Trecho correspondente",
      "intent": "O que o plano precisa mostrar",
      "media_type": "image",
      "source_page_url": "https://example.com/fonte",
      "media_url": "https://example.com/foto.jpg",
      "preview_url": "../media/candidates/S01.jpg",
      "credit": "Autor e fonte a confirmar",
      "rights_status": "pending",
      "publication_rights_approved": false,
      "fit": "Enquadramento proposto",
      "source_in": null,
      "source_out": null,
      "source_text_status": "sem texto incorporado"
    }
  ]
}
```

O exemplo é fictício: não é uma mídia recomendada nem uma licença. Antes da página de aprovação, inspecionar previews e intervalo exato do vídeo. Não aprovar um frame preto/quebrado como se a mídia estivesse validada.

O board exporta hash do manifesto e decisões por ID. Ao trocar origem/crop/intervalo, gere um board novo e revalide os slots alterados; não importar decisões antigas para conteúdo diferente. Decisões ausentes não significam aprovação. Download final só para aprovados. Os termos `approved` e `publication_rights_approved` têm funções distintas.

Créditos: incluir autor/fonte e, quando exigidos, título, link da licença e alterações. Não inventar fotógrafo quando a fonte não informar; manter pendência para conferir antes de publicar. Recorte generativo de retrato requer validação visual e registro do método, sem alegar extração pixel-idêntica.

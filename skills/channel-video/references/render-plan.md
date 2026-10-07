# Contrato de composição

Todos os caminhos de artefatos são relativos à pasta do job. Nada depende de um caminho no computador do autor do kit. Fontes de imagem/vídeo e overlays devem corresponder a slots aprovados, com hash conferido no manifesto. O MP3 precisa de aprovação própria.

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "audio": "audio/take.mp3",
  "avatar": "heygen/avatar.webm",
  "avatar_crop": [0, 0, 1000, 1600],
  "avatar_width_fraction": 0.44,
  "manifest": "media/asset_manifest.json",
  "caption_cues": "transcripts/cues.json",
  "caption_size": 46,
  "caption_center_y_fraction": 0.58,
  "shots": [
    {"id": "S01", "file": "media/approved/asset_000.jpg", "type": "image", "duration": 4.0, "pan": "left", "sharp_fraction": 1.0},
    {"id": "S02", "file": "media/approved/asset_001.mp4", "type": "video", "duration": 4.0, "source_in": 12.0, "sharp_fraction": 0.8}
  ],
  "overlays": [
    {"id": "L01", "file": "media/approved/logo.png", "start": 2.0, "end": 4.0, "x": 650, "y": 160, "width": 280}
  ]
}
```

Valores são apenas um exemplo. O avatar_crop precisa ser medido no WebM real para preservar rosto/busto/mãos e remover padding. O motor não inventa recortes de pessoas nem recupera alpha ausente. Overlays locais precisam estar aprovados como slots do manifesto e possuir alpha quando o layout exigir transparência.

O total das cenas deve coincidir com o áudio a até 0,1 segundo, e o avatar deve ter duração correspondente. O helper não comprime/estica o take para encaixá-lo. `source_in` é o tempo em segundos dentro do arquivo local, não de um vídeo original já aparado. Validar essa distinção para evitar flashes/cortes de outra cena.

`sharp_fraction` entre 0,7 e 1 determina quanto da altura contém a mídia nítida; blur preenche o restante sem distorção. O padrão é quadro totalmente nítido. O enquadramento genérico é central e estável: se cortar o assunto, o agente deve preparar um intervalo/enquadramento melhor antes da montagem, não fingir que o script entende o conteúdo.

`pan` vale `left` ou `right`; fotos são superdimensionadas e movidas continuamente em um quadro oversampled antes de reduzir. Não há zoom pulsante. Cada arquivo de background aparece uma vez. Logo/retrato opcionais têm entrada e saída próprias conforme a fala e o contexto do canal.

As legendas recebem texto dos cues revisados, máximo de duas linhas, e são aplicadas por último. Fonte local é opcional via `CAPTION_FONT_PATH`; o kit usa fonte embutida do Pillow como fallback, não distribui fontes proprietárias. Se o fallback não servir para o idioma/estética, selecionar uma fonte instalada e permitida.

O renderizador não certifica que um WebM é transparente ou que um recorte está bonito. Faça QA visual antes de consolidar. Se a API retornar vídeo opaco, escolher uma saída compatível ou pedir decisão; não compor um retângulo preto sem avisar.

# Controll · Baltigo

Painel de gestão da rede Telegram: inventário, contas, matriz de acessos, audiência e diagnóstico. HTML, CSS e JavaScript sem dependências de produção, fontes remotas ou rastreadores.

## Privacidade antes de publicar

**O snapshot herdado contém convites privados.** A ocultação na interface é apenas visual. Um arquivo servido publicamente pode ser lido por qualquer pessoa; este frontend não implementa autenticação. Não publique a versão completa como uma área privada.

Este redesign não altera convites, permissões, mensagens ou contas no Telegram. Não lê nem inclui arquivos `.session`, credenciais de API ou códigos de login. A remoção de dados do commit atual não os remove automaticamente do histórico Git.

## Usar

Com os arquivos do projeto em um servidor estático, abra `index.html`. Para testar localmente:

```bash
python -m http.server 8000
```

Abra `http://localhost:8000`. Não é necessário `npm install` ou build para o site.

Para abrir com dois cliques, sem servidor, gere a versão portátil:

```bash
python tools/build_portable.py
```

O arquivo `dist/index.html` inclui interface e dados e funciona offline. Trate-o como privado. Uma alternativa sem convites:

```bash
python tools/build_portable.py --without-invites
```

`dist/index_sem_convites.html` remove convites dos campos e descrições. Nomes, IDs e vínculos internos continuam presentes: não é um relatório anônimo.

## Organização

- `index.html`: estrutura da nova interface.
- `assets/controll.css`: sistema visual, layout responsivo e temas.
- `assets/controll.js`: métricas, gráficos SVG, filtros, detalhes, importação e exportação.
- `data/snapshot.html`: arquivo original preservado byte a byte. O novo código lê **apenas** o bloco JSON `embedded-data`; não executa nem injeta o HTML ou JavaScript legado.
- `tools/build_portable.py`: empacota o HTML offline, com opção sem convites.
- `tests/smoke.py`: testes de navegador com Playwright.

O blob original preservado é `81e392ec88662cfbb15ae2317fad3c8f6d34e3a6`. Seu conteúdo não foi reclassificado, completado ou atualizado ao vivo durante o redesign.

## Recursos

Visão consolidada; gráficos de propriedade e visibilidade; tabela pesquisável com filtros por conta, cargo, tipo e visibilidade; ordenação e paginação; painel lateral de detalhes; cartões de contas e matriz Dono/Admin; dispersão de membros versus views; ranking das amostras; diagnóstico; importação local de JSON; exportação CSV/JSON; temas claro e escuro; navegação mobile e atalhos `/` ou `Ctrl/Cmd + K` para busca.

As datas e métricas são da exportação, não de uma conexão ao vivo. Não há classificação automática de animes/mangás nem curvas de crescimento inventadas.

## Critérios de cálculo

O consolidado conta cada Peer ID uma vez e inclui apenas os acessos Dono/Administrador. A soma de membros não representa pessoas únicas. As contas podem compartilhar canais: não some suas audiências individuais.

As métricas agregadas de visualização usam somente canais, não supergrupos. A média por publicação divide a soma dos contadores disponíveis pelo número de mensagens com views nas amostras válidas. Views não são alcance mensal, usuários únicos ou uma série temporal. A seção Diagnóstico preserva as notas de conferência do snapshot original.

## Testes

```bash
pip install playwright
python -m playwright install chromium
python tests/smoke.py
```

Os testes renderizam localmente o HTML gerado em Chromium. Não conectam ao Telegram e não abrem links de convite. O carregador modular foi conferido com uma resposta local simulada do snapshot; não foi feito deploy público nesta alteração.

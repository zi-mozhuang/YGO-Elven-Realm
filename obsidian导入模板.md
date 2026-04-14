---
ID: {{cid}}
卡密: {{id}}
中文名: |-
  {{cn_name}}
YGOPro: |-
  {{sc_name}}
MD: |-
  {{md_name}}
NWBBS: |-
  {{nwbbs_n}}
CNOCG: |-
  {{cnocg_n}}
日文音标: |-
  {{jp_ruby}}
日文名: |-
  {{jp_name}}
英文名: |-
  {{en_name}}
类型: {{text.card_type}}
分类: {{text.category}}
{{#if data.race}}
属性: {{table data.attribute 1 "地" 2 "水" 4 "炎" 8 "风" 16 "光" 32 "暗" 64 "神"}}
级/阶/连: {{data.level}}
种族: {{table data.race 1 "战士" 2 "魔法师" 4 "天使" 8 "恶魔" 16 "不死" 32 "机械" 64 "水" 128 "炎" 256 "岩石" 512 "鸟兽" 1024 "植物" 2048 "昆虫" 4096 "雷" 8192 "龙" 16384 "兽" 32768 "兽战士" 65536 "恐龙" 131072 "鱼" 262144 "海龙" 524288 "爬虫类" 1048576 "念动力" 2097152 "幻神兽" 4194304 "创造神" 8388608 "幻龙" 16777216 "电子界"}}
攻击: {{data.atk}}
防御: {{data.def}}
{{#if text.extra_value}}
连接方向/灵摆值: {{text.extra_value}}
{{/if}}
{{/if}}
兼容: {{data.ot}}
字段:
{{#each (split text.series ",")}}
  - "{{this}}"
{{/each}}
tags: []
---

{{#if id}}
![[ygocard_images/{{id}}.jpg]]
{{else}}
![[view_images/{{cid}}.jpg]]
{{/if}}

**基本信息**  
{{text.types}}

{{#if text.pdesc}}
**灵摆效果**
{{text.pdesc}}
{{/if}}

**效果**  
{{text.desc}}

**描述**  


*关联*  
{{#if data.race}}
地点：
关系：
经历：
{{else}}
地点：
前情：
情节：
{{/if}}

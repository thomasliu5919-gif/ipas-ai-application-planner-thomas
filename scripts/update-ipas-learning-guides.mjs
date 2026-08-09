import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const pageUrl = "https://ipd.nat.gov.tw/ipas/certification/AIAP/learning-resources";
const outputDir = path.resolve("ipas-learning-guides");

const pageResponse = await fetch(pageUrl);
if (!pageResponse.ok) throw new Error(`無法讀取學習資源頁：${pageResponse.status}`);
const html = await pageResponse.text();
const links = [...html.matchAll(/href=["']([^"']+\.pdf)["']/gi)]
  .map((match) => match[1].replaceAll("&amp;", "&"))
  .map((url) => new URL(url, pageUrl).href)
  .filter((url) => /學習指引|勘誤表/i.test(decodeURIComponent(url)))
  .filter((url, index, all) => all.indexOf(url) === index);

if (links.length === 0) throw new Error("頁面未找到學習指引 PDF 連結。");

await mkdir(outputDir, { recursive: true });
const names = [
  "01_初級_科目1_人工智慧基礎概論.pdf",
  "02_初級_科目2_生成式AI應用與規劃.pdf",
  "03_中級_科目1_人工智慧技術應用規劃.pdf",
  "04_中級_科目2_大數據處理分析與應用.pdf",
  "05_中級_科目3_機器學習技術與應用.pdf",
  "06_初級_學習指引勘誤表.pdf",
  "07_中級_學習指引勘誤表.pdf",
];

for (const [index, url] of links.entries()) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`下載失敗：${response.status} ${url}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  await writeFile(path.join(outputDir, names[index] ?? `extra-${index + 1}.pdf`), bytes);
  console.log(`${names[index] ?? `extra-${index + 1}.pdf`}\t${bytes.byteLength} bytes`);
}

console.log(`完成：${links.length} 份，輸出至 ${outputDir}`);

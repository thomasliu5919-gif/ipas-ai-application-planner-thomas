# iPAS AI 應用規劃師｜Thomas 個人備考工作台

這是一個可直接以靜態檔案開啟、也可部署到 GitHub Pages 的個人考試網站，依照參考網站的核心流程設計：科目範圍、練習模式、考試模式、即時解析、錯題複習與本機進度保存。

## 公開部署策略與費用警示

本專案刻意採用以下架構：

- GitHub Pages 靜態託管。
- 公開 GitHub Repository。
- 使用者進度只保存在各自瀏覽器的 `localStorage`。
- 不使用 Firebase、Cloud Firestore、Cloud Functions、付費 API 或後端伺服器。

在不購買自訂網域、且 GitHub 帳號仍使用免費方案的前提下，這個架構不會向你產生網站託管費用。若後續要加入 Firebase 雲端同步、簡訊登入、付費 API、流量型服務或自訂網域，請先確認費用；本專案不會自行建立或綁定任何需要付款的服務。

公開 Repository 會讓程式碼、題庫與放在 Repository 內的學習指引檔案對外可見。發布前請確認其中沒有個人資料、帳號密碼、API Key 或不適合公開的教材檔案。

### GitHub Pages 設定

1. 在 GitHub 建立一個 **Public** Repository。
2. 將本專案檔案推送到 `main` 分支。
3. 進入 Repository 的 `Settings` → `Pages`。
4. 將部署來源選為 `GitHub Actions`。
5. 等待工作流程完成後，使用 GitHub 顯示的 Pages 網址開啟網站。

本專案已附上 `.github/workflows/pages.yml`，不需要 Node.js、npm 或 Firebase 設定即可部署。

## 目前內容

- 依工作區 5 份學習指引建立「學習地圖」與科目章節。
- 將初級／中級勘誤表的重要修正整理成自我檢核題。
- 題目集中在 `questions.js`，可直接新增或改成匯入歷屆題庫。
- 使用 `localStorage` 儲存作答進度與錯題，不需 Firebase 帳號即可個人使用。
- 支援明亮／夜間模式與手機版畫面。
- 初級與中級考試完全分開：各自有獨立入口、科目範圍與模擬考組合。
- 新增「歷屆考題專區」：正式歷屆題與一般學習檢核題分開，支援依初級／中級與年度／梯次建立題組。

目前工作區沒有獨立的歷屆考題檔，因此題目標示為「學習指引檢核」或「勘誤重點」，不是正式歷屆考題。請在取得可使用的歷屆題目檔後，依 `questions.js` 的欄位格式補入。

## 開啟方式

最簡單：直接以瀏覽器開啟 `index.html`。

若要用本機伺服器測試，可在此資料夾執行：

```powershell
python -m http.server 4173
```

再開啟 <http://localhost:4173>。

## 題目格式

每題至少需要：`id`、`subject`、`chapter`、`prompt`、`options`、`answer`、`explanation`、`source`。`answer` 使用選項的 0 起始索引。

## 驗收重點

1. 可由總覽進入開始練習，選擇科目、題數與練習／考試模式。
2. 練習模式會立即顯示答案、解析與來源；考試模式到最後才看結果提示。
3. 答錯的題目會進入錯題複習，答對後會從錯題清單移除。
4. 重新整理頁面後，已完成題目與錯題紀錄仍會保留。
5. 正式歷屆題請依 `past-exams.js` 的 `questionIds` 格式匯入；目前工作區尚未提供正式歷屆題檔，因此專區會顯示待匯入狀態。

import { mkdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { render } from "@react-email/render";
import DigestEmail, { DigestTemplateData } from "./DigestEmail";

const cardBaseStyle =
  "background:#F8FAFF;border-radius:20px;border:1px solid #BFDBFE;padding:24px;margin-bottom:16px;";
const projectTitleStyle = "font-size:18px;color:#3B82F6;margin:0 0 12px 0;font-weight:600;";
const statStyle =
  "display:flex;align-items:center;gap:10px;font-size:15px;color:#1F2937;margin:6px 0;font-weight:500;";

const iconMessage = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h0a8.5 8.5 0 0 1 8.5 8.5Z"/></svg>`;
const iconDocument = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M13 2v7h7"/><path d="M9 13h6"/><path d="M9 17h6"/></svg>`;

const sampleProjectSections = `
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Downtown Highrise Acquisition</p>
    <p style="${statStyle}">${iconMessage}<span><strong>2</strong> new messages (1 mentioned you)</span></p>
    <p style="${statStyle}">${iconDocument}<span><strong>1</strong> new document uploaded</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Seaside Retail Portfolio</p>
    <p style="${statStyle}">${iconMessage}<span><strong>1</strong> new message</span></p>
  </div>
  <div style="${cardBaseStyle}">
    <p style="${projectTitleStyle}">Mesa Industrial Expansion</p>
    <p style="${statStyle}">${iconDocument}<span><strong>2</strong> closing checklists updated</span></p>
  </div>
`;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
const useSampleData = process.env.USE_SAMPLE_DATA === "true";

const sampleData: DigestTemplateData = {
  previewText: "3 updates across Downtown Highrise",
  userName: "Cody Field",
  digestDateLabel: "November 27, 2025",
  ctaUrl: "https://capmatch.com/dashboard",
  managePrefsUrl: "https://capmatch.com/settings/notifications",
  projectSectionsHtml: sampleProjectSections,
};

const html = await render(
  <DigestEmail {...(useSampleData ? sampleData : {})} />,
  {
    pretty: true,
  }
);

  const distDir = join(__dirname, "dist");
  mkdirSync(distDir, { recursive: true });

  const outputPath = join(distDir, "digest-template.html");
  writeFileSync(outputPath, html, { encoding: "utf-8" });

  console.log(`Digest template rendered to ${outputPath}`);
}

main().catch((err) => {
  console.error("Failed to render digest template:", err);
  process.exit(1);
});


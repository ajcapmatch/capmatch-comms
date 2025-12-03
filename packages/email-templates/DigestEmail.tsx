import type { CSSProperties } from "react";
import {
  Body,
  Column,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Row,
  Section,
  Text,
} from "@react-email/components";

const progressBlue = "#3B82F6";
const progressBlueLight = "#60A5FA";
const textColor = "#0F172A";
const fontStack = '\'TASA Orbiter\', "Inter", "Helvetica Neue", Arial, sans-serif';

export const PROJECT_SECTIONS_MARKER = "<!--PROJECT_SECTIONS-->";

export type DigestTemplateData = {
  previewText: string;
  userName: string;
  digestDateLabel: string;
  ctaUrl: string;
  managePrefsUrl: string;
  projectSectionsHtml: string;
};

const defaultTemplateData: DigestTemplateData = {
  previewText: "{{PREVIEW_TEXT}}",
  userName: "{{USER_NAME}}",
  digestDateLabel: "{{DIGEST_DATE}}",
  ctaUrl: "{{CTA_URL}}",
  managePrefsUrl: "{{MANAGE_PREFS_URL}}",
  projectSectionsHtml: PROJECT_SECTIONS_MARKER,
};

export default function DigestEmail(props: Partial<DigestTemplateData>) {
  const data: DigestTemplateData = { ...defaultTemplateData, ...props };

  return (
    <Html>
      <Head>
        <style>
          {`
            @media screen and (max-width: 600px) {
              .container {
                width: 100% !important;
                padding: 24px !important;
                border-radius: 16px !important;
              }
              .content-padding {
                padding: 24px !important;
              }
              .header-row,
              .hero,
              .cta-section {
                padding: 0 !important;
              }
              .logo-img {
                width: 56px !important;
                height: auto !important;
                margin-top: 20px !important;
              }
              .hero {
                padding: 24px !important;
                border-radius: 20px !important;
              }
              .hero-copy {
                font-size: 19px !important;
                line-height: 28px !important;
              }
              .cta-section {
                padding: 0 4px 24px !important;
              }
              .cta-button {
                display: block !important;
                width: 100% !important;
                box-sizing: border-box !important;
              }
            }
          `}
        </style>
      </Head>
      <Preview>{data.previewText}</Preview>
      <Body style={body}>
        <Container style={container} className="container">
          <Section style={header} className="header-row">
            <Row>
              <Column>
                <Text style={eyebrow}>CAPMATCH</Text>
                <Heading style={headline}>Daily Digest</Heading>
                <Text style={subhead}>Important activity across your projects.</Text>
              </Column>
              <Column style={logoColumn}>
                <Img
                  src="https://capmatch.com/CapMatchLogo.png"
                  alt="CapMatch"
                  width="64"
                  height="64"
                  style={logoImg}
                  className="logo-img"
                />
              </Column>
            </Row>
          </Section>

          <Section style={hero} className="hero">
            <Text style={heroCopy} className="hero-copy">
              Hey <span style={heroUser}>{data.userName}</span>, here&apos;s what happened on{" "}
              <strong>{data.digestDateLabel}</strong>.
            </Text>
          </Section>

          <Section>
            <div
              dangerouslySetInnerHTML={{
                __html: data.projectSectionsHtml,
              }}
            />
          </Section>

          <Section style={ctaSection} className="cta-section">
            <Link href={data.ctaUrl} style={ctaButton} className="cta-button">
              Open CapMatch →
            </Link>
          </Section>

          <Hr style={divider} />

          <Section style={footer}>
            <Text style={footerText}>
              You&apos;re receiving this email because digest alerts are enabled.{" "}
              <Link href={data.managePrefsUrl} style={footerLink}>
                Manage preferences
              </Link>
              .
            </Text>
          </Section>
        </Container>
      </Body>
    </Html>
  );
}

const body: CSSProperties = {
  backgroundColor: "#F4F6FB",
  padding: "24px",
  fontFamily: fontStack,
  color: textColor,
};

const container: CSSProperties = {
  width: "100%",
  maxWidth: "640px",
  margin: "0 auto",
  backgroundColor: "#FFFFFF",
  borderRadius: "24px",
  padding: "40px 48px",
  boxShadow: "0 20px 55px rgba(15, 23, 42, 0.14)",
};

const header: CSSProperties = {
  marginBottom: "32px",
};

const eyebrow: CSSProperties = {
  fontSize: "12px",
  letterSpacing: "0.4em",
  color: textColor,
  margin: "0 0 8px 0",
  fontWeight: 600,
};

const headline: CSSProperties = {
  fontSize: "32px",
  lineHeight: "36px",
  color: textColor,
  margin: 0,
};

const subhead: CSSProperties = {
  fontSize: "16px",
  color: textColor,
  marginTop: "6px",
};

const logoColumn: CSSProperties = {
  textAlign: "right",
};

const logoImg: CSSProperties = {
  width: "80px",
  height: "64px",
};

const hero: CSSProperties = {
  background: "linear-gradient(135deg, #F8FAFF, #E0EDFF)",
  borderRadius: "28px",
  padding: "36px",
  marginBottom: "36px",
  border: "1px solid #DBEAFE",
  boxShadow: "0 25px 45px rgba(15, 23, 42, 0.08)",
};

const heroCopy: CSSProperties = {
  color: textColor,
  fontSize: "22px",
  fontWeight: 600,
  margin: 0,
};

const heroUser: CSSProperties = {
  color: textColor,
  fontWeight: 600,
};

const ctaSection: CSSProperties = {
  textAlign: "center",
  marginTop: "24px",
  padding: "0 16px",
};

const ctaButton: CSSProperties = {
  backgroundColor: progressBlue,
  color: textColor,
  padding: "14px 32px",
  borderRadius: "999px",
  fontWeight: 600,
  textDecoration: "none",
  display: "inline-block",
  fontSize: "16px",
  width: "100%",
  maxWidth: "360px",
};

const ctaHint: CSSProperties = {
  color: textColor,
  fontSize: "13px",
  marginTop: "12px",
};

const divider: CSSProperties = {
  borderColor: "#E2E8F0",
  margin: "32px 0",
};

const footer: CSSProperties = {
  textAlign: "center",
};

const footerText: CSSProperties = {
  color: textColor,
  fontSize: "12px",
  margin: "4px 0",
};

const footerLink: CSSProperties = {
  color: textColor,
  textDecoration: "none",
};


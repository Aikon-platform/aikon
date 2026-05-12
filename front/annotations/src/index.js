import Mirador from 'mirador';
import Mae, { annotationAdapters } from "mirador-annotation-editor";
import 'react-quill/dist/quill.snow.css';

const iiifAnnotationVersion = 2;
const { AiiinotateAdapter } = annotationAdapters;
console.log("MAE", AiiinotateAdapter);

const
  windowUrl = new URL(window.location.href),
  iiifManifest = windowUrl.searchParams.get("iiif-content"),
  iiifCanvasIndex = windowUrl.searchParams.get("canvas");

// NOTE we could also use AIIINOTATE_PUBLIC_URL
let aiiinotateBaseUrl;
if ( process.env.TARGET === "prod" && (process.env.DOCKER || "").toLocaleLowerCase() === "true" ) {
  aiiinotateBaseUrl = `https://${process.env.PROD_URL}/aiiinotate`
} else {
  aiiinotateBaseUrl = process.env.AIIINOTATE_BASE_URL
}

const config = {
  id: 'miradorRoot',
  language: 'en',
  annotation: {
    adapter: (canvasId) => {
      return new AiiinotateAdapter(aiiinotateBaseUrl, iiifAnnotationVersion, canvasId)
    },
    allowTargetShapesStyling: true,
    commentTemplates: [{
      content: '<h4>Comment</h4><p>Comment content</p>',
      title: 'Template',
    },
    {
      content: '<h4>Comment2</h4><p>Comment content</p>',
      title: 'Template 2',
    }],
    debug: true,
    exportLocalStorageAnnotations: true,
    readonly: false,
    tagsSuggestions: ['Illustration', 'Diagram'],
  },
  annotations: {
    htmlSanitizationRuleSet: 'liberal',
  },
  themes: {
    dark: {
      typography: {
        formSectionTitle: {
          color: '#4258ff',
          fontSize: '1rem',
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        },
        subFormSectionTitle: {
          fontSize: '1.383rem',
          fontWeight: 300,
          letterSpacing: '0em',
          lineHeight: '1.33em',
          textTransform: 'uppercase',
        },
      },
    },
    light: {
      palette: {
        primary: {
          main: '#4258ff',
        },
      },
      typography: {
        formSectionTitle: {
          color: '#4258ff',
          fontSize: '1.215rem',
        },
        subFormSectionTitle: {
          fontSize: '0.937rem',
          fontWeight: 300,

        },
      },
    },
  },
  window: {
    defaultSideBarPanel: 'annotations',
    sideBarOpenByDefault: true,
  },
  windows: [
    {
      manifestId: iiifManifest,
      canvasIndex: iiifCanvasIndex
    },
  ],
};

Mirador.viewer(config, [Mae]);

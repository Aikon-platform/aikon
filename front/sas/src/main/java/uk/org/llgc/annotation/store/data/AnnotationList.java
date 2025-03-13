package uk.org.llgc.annotation.store.data;

import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import java.io.IOException;

import org.apache.jena.rdf.model.Model;

import uk.org.llgc.annotation.store.AnnotationUtils;

public class AnnotationList {
    protected List<Annotation> _annotations = null;
    protected String _id = "";

    public AnnotationList() {
        _annotations = new ArrayList<Annotation>();
    }

    public AnnotationList(final List<Map<String, Object>> pAnnos) {
        _annotations = new ArrayList<Annotation>();
        for (Map<String,Object> tAnno : pAnnos) {
            _annotations.add(new Annotation(tAnno));
        }
    }

    public AnnotationList(final List<Model> pAnnotations, final boolean pCompact) throws IOException {
        _annotations = new ArrayList<Annotation>();
        AnnotationUtils tUtils = new AnnotationUtils();
        for (Model tModel : pAnnotations) {
            _annotations.add(new Annotation(tUtils.frameAnnotation(tModel, pCompact)));
        }
    }

    /**
     * Get id.
     *
     * @return id as String.
     */
    public String getId() {
        return _id;
    }

    /**
     * Set id.
     *
     * @param id the value to set.
     */
    public void setId(final String pId) {
         _id = pId;
    }

    public void add(final Annotation pAnno) {
        _annotations.add(pAnno);
    }

    public Annotation get(final String pAnnoId) {
        for (Annotation tAnno : _annotations) {
            if (tAnno.getId().equals(pAnnoId)) {
                return tAnno;
            }
        }
        return null;
    }

    public int size() {
        return _annotations.size();
    }

    public List<Annotation> getAnnotations() {
        return _annotations;
    }

    public void setAnnotations(final List<Annotation> pAnnos) {
        _annotations = pAnnos;
    }

    public Map<String, Object> toJson() throws IOException {
        Map<String,Object> tJson = new HashMap<String,Object>();
        tJson.put("@context", "http://iiif.io/api/presentation/2/context.json");
        tJson.put("@id", _id);
        tJson.put("@type", "sc:AnnotationList");

        List<Map<String,Object>> tAnnos = new ArrayList<Map<String,Object>>();
        tJson.put("resources", tAnnos);

        for (Annotation tAnno: _annotations) {
            tAnnos.add(tAnno.toJson());
        }

        return tJson;
    }

}

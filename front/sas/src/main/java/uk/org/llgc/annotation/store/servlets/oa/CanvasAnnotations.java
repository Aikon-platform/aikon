package uk.org.llgc.annotation.store.servlets.oa;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.IOException;
import java.io.File;

import com.github.jsonldjava.utils.JsonUtils;

import org.apache.jena.rdf.model.Model;

import java.util.Map;
import java.util.List;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;

import uk.org.llgc.annotation.store.adapters.StoreAdapter;
import uk.org.llgc.annotation.store.encoders.Encoder;
import uk.org.llgc.annotation.store.data.AnnotationList;
import uk.org.llgc.annotation.store.data.Canvas;
import uk.org.llgc.annotation.store.AnnotationUtils;
import uk.org.llgc.annotation.store.StoreConfig;

import uk.org.llgc.annotation.store.exceptions.MalformedAnnotation;

public class CanvasAnnotations extends HttpServlet {
	protected static Logger _logger = LogManager.getLogger(CanvasAnnotations.class.getName());
	protected AnnotationUtils _annotationUtils = null;
	protected StoreAdapter _store = null;

	public void init(final ServletConfig pConfig) throws ServletException {
		super.init(pConfig);
		Encoder tEncoder = StoreConfig.getConfig().getEncoder();
		_annotationUtils = new AnnotationUtils(new File(super.getServletContext().getRealPath("/contexts")), tEncoder);
		_store = StoreConfig.getConfig().getStore();
		_store.init(_annotationUtils);
	}

	public void doGet(final HttpServletRequest pReq, final HttpServletResponse pRes) throws IOException {
		_logger.debug("Annotations for page: " + pReq.getParameter("uri"));
		_logger.debug("media " + pReq.getParameter("media"));
		_logger.debug("limit " + pReq.getParameter("limit"));
		if (pReq.getParameter("uri") == null || pReq.getParameter("uri").trim().length() == 0) {
			return; // for some reason Mirador is sending blank uri requests
		}
        AnnotationList tAnnoList = _store.getAnnotationsFromPage(new Canvas(pReq.getParameter("uri"), ""));

        pRes.setContentType("application/ld+json; charset=UTF-8");
        pRes.setCharacterEncoding("UTF-8");
        /**/_logger.debug(JsonUtils.toPrettyString(tAnnoList.toJson().get("resources")));
        pRes.getWriter().println(JsonUtils.toPrettyString(tAnnoList.toJson().get("resources")));
    }
}

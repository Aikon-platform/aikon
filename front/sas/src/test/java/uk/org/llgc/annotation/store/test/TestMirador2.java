package uk.org.llgc.annotation.store.test;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.Rule;
import org.junit.Before;
import org.junit.After;
import org.junit.rules.TemporaryFolder;

import com.github.jsonldjava.utils.JsonUtils;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.Iterator;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;

import uk.org.llgc.annotation.store.exceptions.IDConflictException;
import uk.org.llgc.annotation.store.data.Annotation;
import uk.org.llgc.annotation.store.data.AnnotationList;
import uk.org.llgc.annotation.store.adapters.StoreAdapter;
import uk.org.llgc.annotation.store.encoders.Mirador214;
import uk.org.llgc.annotation.store.AnnotationUtils;
import uk.org.llgc.annotation.store.StoreConfig;
import uk.org.llgc.annotation.store.exceptions.IDConflictException;
import uk.org.llgc.annotation.store.exceptions.MalformedAnnotation;

import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.riot.Lang;
import org.apache.jena.rdf.model.StmtIterator;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.rdf.model.Statement;
import org.apache.jena.rdf.model.Resource;
import org.apache.jena.rdf.model.Statement;
import org.apache.jena.vocabulary.DCTerms;
import org.apache.jena.query.* ;

import org.openrdf.repository.http.HTTPRepository;
import org.openrdf.repository.RepositoryConnection;
import org.openrdf.repository.RepositoryException;

import java.util.Properties;

import java.net.URISyntaxException;

public class TestMirador2 extends TestUtils {
	protected static Logger _logger = LogManager.getLogger(TestMirador2.class.getName());

	public TestMirador2() throws IOException {
		super();
	}

	@Before
   public void setup() throws IOException {
		super.setup();
	}

   @After
   public void tearDown() throws IOException {
		super.tearDown();
	}

	@Test
	public void TestMirador2() throws IOException, IDConflictException, InterruptedException, MalformedAnnotation {
		Map<String, Object> tAnnotationJSON = _annotationUtils.readAnnotaion(new FileInputStream(getClass().getResource("/jsonld/testAnnotation.json").getFile()), StoreConfig.getConfig().getBaseURI(null));

		String tAnnoId = (String)tAnnotationJSON.get("@id");
		_logger.debug("ID " + tAnnoId);
		Annotation tAnno = _store.addAnnotation(new Annotation(tAnnotationJSON));

		Map<String, Object> tAnnoJson = tAnno.toJson();

		// Require on to be an map for mirador 2
		assertTrue("On needs to be a Map in Mirador2 and it isn't.", tAnnoJson.get("on") instanceof Map);

		//System.out.println(JsonUtils.toPrettyString(tAnnotation));
		assertNotNull("FragmentSelector present", ((Map<String,Map<String,String>>)tAnnoJson.get("on")).get("selector").get("value"));
	}

    @Test
    public void testPopulate() throws IOException, IDConflictException, InterruptedException, MalformedAnnotation {
        List<Map<String, Object>> tAnnotationListJSON = _annotationUtils.readAnnotationList(new FileInputStream(getClass().getResource("/jsonld/annos_master_version1.json").getFile()), StoreConfig.getConfig().getBaseURI(null)); //annotaiton list

        AnnotationList tList = new AnnotationList(tAnnotationListJSON);
        AnnotationList tAnnotations = _store.addAnnotationList(tList);

        assertEquals("Exported list was a different size to the one supplied.", tAnnotationListJSON.size(), tAnnotations.getAnnotations().size());

        Map<String,Object> tAnno1 = tAnnotations.getAnnotations().get(0).toJson();
		assertTrue("For Mirador 2 on doesn't need to be an array ", tAnno1.get("on") instanceof Map);

        Map<String,Object> tOn = (Map<String,Object>)tAnno1.get("on");
        Map<String,Object> tSelector = (Map<String,Object>)tOn.get("selector");
        assertEquals("Mirador requires this to be a fragment selector but selector was:", "oa:FragmentSelector",tSelector.get("@type"));
    }

    @Test
	public void TestNoBlankNode() throws IOException, IDConflictException, InterruptedException, MalformedAnnotation {
		Map<String, Object> tAnnotationJSON = _annotationUtils.readAnnotaion(new FileInputStream(getClass().getResource("/jsonld/testAnnotation.json").getFile()), StoreConfig.getConfig().getBaseURI(null));

		Annotation tAnno = _store.addAnnotation(new Annotation(tAnnotationJSON));

		Map<String, Object> tAnnotation = tAnno.toJson();

		// Require on to be an map for mirador 2
		assertTrue("On needs to be a Map in Mirador2 and it isn't.", tAnnotation.get("on") instanceof Map);

		//System.out.println(JsonUtils.toPrettyString(tAnnotation));
		assertFalse("Annotation shouldn't have a blank node in on: " + ((Map<String,Map<String,String>>)tAnnotation.get("on")), ((Map<String,Map<String,String>>)tAnnotation.get("on")).containsKey("@id"));
	}

}

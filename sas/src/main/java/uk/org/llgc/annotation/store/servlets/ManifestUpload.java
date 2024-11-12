package uk.org.llgc.annotation.store.servlets;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;

import java.io.IOException;
import java.io.File;
import java.io.InputStream;
import java.io.FileWriter;
import java.io.FileReader;
import java.io.FilenameFilter;
import java.io.BufferedReader;
import java.net.URL;
import java.net.HttpURLConnection;

import java.net.URL;

import java.util.Map;
import java.util.List;
import java.util.HashMap;
import java.util.ArrayList;

import com.github.jsonldjava.utils.JsonUtils;

import org.apache.jena.rdf.model.Model;

import uk.org.llgc.annotation.store.adapters.StoreAdapter;
import uk.org.llgc.annotation.store.encoders.Encoder;
import uk.org.llgc.annotation.store.exceptions.IDConflictException;
import uk.org.llgc.annotation.store.data.ManifestProcessor;
import uk.org.llgc.annotation.store.data.Manifest;
import uk.org.llgc.annotation.store.AnnotationUtils;
import uk.org.llgc.annotation.store.StoreConfig;

public class ManifestUpload extends HttpServlet {
    protected static Logger _logger = LogManager.getLogger(ManifestUpload.class.getName());
    protected AnnotationUtils _annotationUtils = null;
    protected StoreAdapter _store = null;

    public void init(final ServletConfig pConfig) throws ServletException {
        super.init(pConfig);
        Encoder tEncoder = StoreConfig.getConfig().getEncoder();
        _annotationUtils = new AnnotationUtils(new File(super.getServletContext().getRealPath("/contexts")), tEncoder);
        _store = StoreConfig.getConfig().getStore();
        _store.init(_annotationUtils);
    }

    // Add proxy configuration
    static {
        String httpProxy = System.getenv("HTTP_PROXY");
        String httpsProxy = System.getenv("HTTPS_PROXY");
        String noProxy = System.getenv("NO_PROXY");

        if (httpProxy != null && !httpProxy.isEmpty()) {
            try {
                URL proxyUrl = new URL(httpProxy);
                System.setProperty("http.proxyHost", proxyUrl.getHost());
                System.setProperty("http.proxyPort", String.valueOf(proxyUrl.getPort()));
            } catch (Exception e) {
                _logger.error("Failed to parse HTTP_PROXY: " + e.getMessage());
            }
        }

        if (httpsProxy != null && !httpsProxy.isEmpty()) {
            try {
                URL proxyUrl = new URL(httpsProxy);
                System.setProperty("https.proxyHost", proxyUrl.getHost());
                System.setProperty("https.proxyPort", String.valueOf(proxyUrl.getPort()));
            } catch (Exception e) {
                _logger.error("Failed to parse HTTPS_PROXY: " + e.getMessage());
            }
        }

        if (noProxy != null && !noProxy.isEmpty()) {
            System.setProperty("http.nonProxyHosts", noProxy.replace(",", "|"));
        }
    }

    public void doPost(final HttpServletRequest pReq, final HttpServletResponse pRes) throws IOException {
        String tID = "";
        Map<String, Object> tManifestJson = null;
        if (pReq.getParameter("uri") != null) {
            tID = pReq.getParameter("uri");
            _logger.info("Fetching manifest from: " + tID);

            // Use HttpURLConnection with timeout settings
            URL url = new URL(tID);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(30000); // 30 seconds
            conn.setReadTimeout(30000);    // 30 seconds

            try {
                tManifestJson = (Map<String,Object>)JsonUtils.fromInputStream(conn.getInputStream());
            } catch (Exception e) {
                _logger.error("Failed to fetch manifest: " + e.getMessage(), e);
                pRes.sendError(HttpServletResponse.SC_BAD_GATEWAY, "Failed to fetch manifest: " + e.getMessage());
                return;
            } finally {
                conn.disconnect();
            }
        } else {
            InputStream tManifestStream = pReq.getInputStream();
            tManifestJson = (Map<String,Object>)JsonUtils.fromInputStream(tManifestStream);
        }

        try {
            Manifest tManifest = new Manifest(tManifestJson, null);
            String tShortId = _store.indexManifest(tManifest);
            Map<String,Object> tJson = new HashMap<String,Object>();
            Map<String,String> tLinks = new HashMap<String,String>();
            tJson.put("loaded", tLinks);
            tLinks.put("uri", tManifest.getURI());
            tLinks.put("short_id", tManifest.getShortId());

            pRes.setContentType("application/json");
            pRes.setCharacterEncoding("UTF-8");
            JsonUtils.write(pRes.getWriter(), tJson);
        } catch (Exception e) {
            _logger.error("Failed to process manifest: " + e.getMessage(), e);
            pRes.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Failed to process manifest: " + e.getMessage());
        }
    }
}

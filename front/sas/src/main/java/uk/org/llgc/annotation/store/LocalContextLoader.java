package uk.org.llgc.annotation.store;

import com.github.jsonldjava.core.RemoteDocument;
import com.github.jsonldjava.core.DocumentLoader;
import com.github.jsonldjava.utils.JsonUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.File;
import java.io.FileInputStream;
import java.net.URL;
import java.util.Map;
import java.util.HashMap;

public class LocalContextLoader extends DocumentLoader {
    protected static Logger _logger = LogManager.getLogger(LocalContextLoader.class.getName());
    private final File contextsDir;
    private final Map<String, String> contextMappings;

    public LocalContextLoader(File contextsDir) {
        this.contextsDir = contextsDir;
        this.contextMappings = new HashMap<>();
        this.contextMappings.put("http://iiif.io/api/presentation/2/context.json", "presentation.json");
        this.contextMappings.put("http://iiif.io/api/image/2/context.json", "image.json");
        _logger.info("LocalContextLoader initialized with contexts directory: " + contextsDir.getAbsolutePath());
    }

    @Override
    public RemoteDocument loadDocument(String url) throws Exception {
        String localFile = contextMappings.get(url);
        if (localFile != null) {
            File contextFile = new File(contextsDir, localFile);
            if (contextFile.exists()) {
                _logger.info("Loading context from local file: " + contextFile.getAbsolutePath());
                try (FileInputStream fis = new FileInputStream(contextFile)) {
                    Object document = JsonUtils.fromInputStream(fis);
                    return new RemoteDocument(url, document);
                }
            } else {
                _logger.warn("Local context file not found: " + contextFile.getAbsolutePath() + ", falling back to remote URL");
            }
        }
        _logger.info("Loading context from remote URL: " + url);
        return super.loadDocument(url);
    }
}

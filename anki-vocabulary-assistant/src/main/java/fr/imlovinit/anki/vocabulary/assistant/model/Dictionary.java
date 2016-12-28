package fr.imlovinit.anki.vocabulary.assistant.model;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import fr.imlovinit.anki.vocabulary.assistant.util.Json;

import java.io.IOException;

public class Dictionary {

    private String filepath;
    private ArrayNode dictionary;

    public Dictionary(String filepath) {
        this.filepath = filepath;
        this.dictionary = loadDictionary();
    }

    private ArrayNode loadDictionary() {
        try {
            ArrayNode rootNode = Json.readFromFile(filepath, ArrayNode.class);
            return rootNode;
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * Search inside the full JSON dictionary after the given identifier.
     * Only the rank could be used as identifier for now.
     */
    public Word searchWord(String identifier) {
        ObjectNode json = (ObjectNode) dictionary.get(Integer.parseInt(identifier) - 1);
        fix(json);
        return new Word(json);
    }

    /**
     * Fix bugs in the Python program having generated the dictionary file.
     *
     * @return the updated JSON document
     */
    private void fix(ObjectNode json) {
        // IPA could contains multiple IPA text (Ex: /car/ in US, /cAr/). We keep only the first one
        if (json.has("ipa")) {
            String ipa = json.get("ipa").asText();
            int indexSecondSlash = ipa.indexOf('/', 1);
            if (indexSecondSlash < ipa.length() - 1) {
                ipa = ipa.substring(0, indexSecondSlash + 1);
                json.set("ipa", TextNode.valueOf(ipa));
            }
        }

        // Thumbnails are configured as 600px but many pictures are not so width
        if (json.has("images")) {
            ArrayNode images = (ArrayNode) json.get("images");
            for (int i = 0; i < images.size(); i++) {
                ObjectNode image = (ObjectNode) images.get(i);
                image.put("thumb_url", image.get("thumb_url").asText().replace("600px", "100px"));
            }
        }
    }

}

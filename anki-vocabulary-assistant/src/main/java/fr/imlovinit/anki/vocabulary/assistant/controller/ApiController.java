package fr.imlovinit.anki.vocabulary.assistant.controller;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.google.api.services.customsearch.model.Result;
import fr.imlovinit.anki.vocabulary.assistant.util.Json;
import fr.imlovinit.anki.vocabulary.assistant.model.Dictionary;
import fr.imlovinit.anki.vocabulary.assistant.model.Word;
import fr.imlovinit.anki.vocabulary.assistant.service.CseService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api")
public class ApiController {

    private final Logger log = LoggerFactory.getLogger(ApiController.class);

    private Dictionary dictionary;

    @Value("${outputDir}")
    private String outputDir;

    @Value("${dictionaryFile}")
    private String dictionaryFile;

    @Autowired
    private CseService cse;

    @PostConstruct
    public void init() {
        dictionary = new Dictionary(dictionaryFile);
    }

    @RequestMapping(path = "/word/{identifier}", method = RequestMethod.GET, produces = "application/json")
    public ObjectNode getWord(
    		@PathVariable String identifier) {
        return dictionary.searchWord(identifier).asJsonNode();
    }

    @RequestMapping(path = "/images/{query}", method = RequestMethod.GET, produces = "application/json")
    public List<Result> getImages(
            @PathVariable String query) {
        return cse.searchImages(query);
    }

    @RequestMapping(path = "/word/{identifier}", method = RequestMethod.PUT, consumes = "application/json")
    public void saveWord(
            @PathVariable String identifier,
            @RequestBody String jsonWord) throws IOException {

        Word originalWord = dictionary.searchWord(identifier);

        System.out.println("Saving word " + identifier);

        ObjectNode node = Json.readFromString(jsonWord, ObjectNode.class);
        Word newWord = new Word(node);

        // Save picture
        newWord.save(outputDir);
    }


}
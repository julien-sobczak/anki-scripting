package fr.imlovinit.anki.vocabulary.assistant.util;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.File;
import java.io.IOException;

public class Json {

    public static ObjectMapper mapper = createMapper();

    public static ObjectMapper createMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.enable(SerializationFeature.INDENT_OUTPUT);
        return mapper;
    }

    public static <T extends JsonNode> T readFromFile(String filepath, Class<T> clazz) throws IOException {
        return (T) mapper.readTree(new File(filepath));
    }

    public static <T extends JsonNode> T readFromString(String json, Class<T> clazz) throws IOException {
        return mapper.readValue(json, clazz);
    }

    public static void writeToFile(JsonNode json, String filepath) throws IOException {
        mapper.writeValue(new File(filepath), json);
    }

}

package fr.imlovinit.anki.vocabulary.assistant.model;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import fr.imlovinit.anki.vocabulary.assistant.util.Json;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.net.URL;

public class Word {

    private final Logger log = LoggerFactory.getLogger(Word.class);

    private static final int MAX_THUMB_WIDTH = 400;

    private ObjectNode word;

    public Word(ObjectNode json) {
        this.word = json;
    }

    public String getImageUrl() {
        // Search the selected image
        ArrayNode images = (ArrayNode) word.get("images");
        if (images != null) {
            for (int i = 0; i < images.size(); i++) {
                ObjectNode image = (ObjectNode) images.get(i);
                if (image.get("include") != null && image.get("include").asBoolean()) {
                    String url = image.get("url").asText();
                    return url;
                }
            }
        }

        return null; // No selected image
    }

    public String getAudioUrl() {
        // Search the selected image
        ObjectNode audio = (ObjectNode) word.get("audio");
        if (audio != null) {
            if (audio.get("include") != null && audio.get("include").asBoolean()) {
                String url = audio.get("url").asText();
                return url;
            }
        }

        return null; // No audio file or not selected
    }

    public String getDescriptiveName() {
        return word.get("rank").asInt() + "-" + word.get("title").asText();
    }

    private String getDictionaryEntryFilename() {
        return getDescriptiveName() + ".json";
    }

    private String getImageFilename(String url) {
        String extension = extractExtension(url);
        return getDescriptiveName() + "." + extension;
    }

    private String getThumbFilename() {
        return getDescriptiveName() + "-thumb.jpg";
    }

    private String getAudioFilename(String url) {
        String extension = extractExtension(url);
        return getDescriptiveName() + "." + extension;
    }

    private static String extractExtension(String url) {
        int indexDot = url.lastIndexOf('.');
        int indexPercent = url.indexOf('?', indexDot);
        String extension = indexPercent == -1 ? url.substring(indexDot + 1) : url.substring(indexDot + 1, indexPercent);
        return extension;
    }

    private void saveDictionaryEntry(String outputDir) throws IOException {
        String filepath = outputDir + File.separator + getDictionaryEntryFilename();
        Json.writeToFile(asJsonNode(), filepath);
        System.out.println("Saved to " + filepath);

    }

    private void downloadPicture(String outputDir) throws IOException {
        String imageUrl = getImageUrl();

        if (imageUrl != null) {
            // Download the picture locally
            String originalFilepath = outputDir + File.separator + getImageFilename(imageUrl);
            downloadFile(imageUrl, originalFilepath);

            // Resize the picture
            String thumbFilepath = outputDir + File.separator + getThumbFilename();
            resizePicture(originalFilepath, thumbFilepath);
        }
    }

    private void downloadAudio(String outputDir) throws IOException {
        String audioUrl = getAudioUrl();

        if (audioUrl != null) {
            String filepath = outputDir + File.separator + getAudioFilename(audioUrl);
            downloadFile(audioUrl, filepath);
        }
    }

    private void resizePicture(String originalFilepath, String thumbFilepath) throws IOException {
        // Implementation: We use AWT library to resize our picture.
        BufferedImage image = ImageIO.read(new File(originalFilepath));

        double imageHeight = image.getHeight();
        double imageWidth = image.getWidth();

        double scaledHeight = imageHeight;
        double scaledWidth = imageWidth;

        if (imageWidth > MAX_THUMB_WIDTH) {
            scaledWidth = MAX_THUMB_WIDTH;
            scaledHeight =  imageHeight * MAX_THUMB_WIDTH / imageWidth;
        }

        BufferedImage resizedImage = new BufferedImage((int) scaledWidth, (int) scaledHeight, image.getType());
        Graphics2D g = resizedImage.createGraphics();
        g.drawImage(image, 0, 0, (int) scaledWidth, (int) scaledHeight, null);
        g.dispose();

        ImageIO.write(resizedImage, "jpg", new File(thumbFilepath));
    }

    private void downloadFile(String url, String outputPath) throws IOException {

        if (new File(outputPath).exists()) {
            log.info("Not downloading file {}. File already exists.", outputPath);
            return;
        }

        URL link = new URL(url);

        InputStream in = new BufferedInputStream(link.openStream());
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[1024];
        int n = 0;
        while (-1 != (n = in.read(buf))) {
            out.write(buf, 0, n);
        }
        out.close();
        in.close();
        byte[] response = out.toByteArray();

        FileOutputStream fos = new FileOutputStream(outputPath);
        fos.write(response);
        fos.close();

        log.info("Successfully downloaded file {}", outputPath);
    }

    public void save(String outputDir) throws IOException {
        downloadPicture(outputDir);
        downloadAudio(outputDir);
        saveDictionaryEntry(outputDir);
    }

    public ObjectNode asJsonNode() {
        return word;
    }

}

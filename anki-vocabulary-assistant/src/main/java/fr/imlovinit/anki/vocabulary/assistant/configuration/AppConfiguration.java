package fr.imlovinit.anki.vocabulary.assistant.configuration;


import fr.imlovinit.anki.vocabulary.assistant.service.CseService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AppConfiguration {

    @Value("${developerKey}")
    private String developerKey;

    @Value("${cx}")
    private String cx;

    @Bean public CseService cseService() {
        System.out.println("Creating Google CSE client...");
        System.out.println("\t- Developer key=" + developerKey);
        System.out.println("\t- CX=" + cx);
        return new CseService(developerKey, cx);
    }

}

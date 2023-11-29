package com.example.cokkiri.model;

import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
public class NoShowClassMatchList {
    @Id
    @Column
    private int matchingId;

    @Column
    private String email;

    @Column
    private  String matchingType;

    @Column
    private LocalDateTime restrictionTime;
}

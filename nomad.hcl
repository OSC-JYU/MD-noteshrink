job "md-noteshrink" {
  type = "service"

  group "MD-bertopic" {
    count = 1

    restart {
      attempts = 2
      interval = "5m"
      delay    = "15s"
      mode     = "fail"
    }

    reschedule {
      attempts       = 2
      interval       = "10m"
      delay          = "30s"
      delay_function = "constant"
      unlimited      = false
    }

    network {
      port "node" {
        to = 9023
      }
    }

    service {
      name     = "md-noteshrink"
      port     = "node"
      provider = "nomad"
      
      check {
        type     = "http"
        path     = "/health"
        interval = "10s"
        timeout  = "3s"
      }
    }

    task "md-noteshrink" {
      driver = "podman"
      config {
          image = "localhost/messydesk/md-noteshrink:0.2"
          force_pull = false
          ports = ["node"]
          # Disk mode: the service reads and writes MessyDesk's data directory. Adjust the host paths.
          volumes = [
            "/srv/messydesk:/md",
          ]
      }
      env {
        PORT = "9023"
        MD_PATH = "/md"
      }
      resources {
        memory = 1000  # Memory in MB
        cpu    = 500  # CPU shares (500 = 50% of 1 CPU)
      }
    }
  }
}
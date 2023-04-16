import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';
import { NgxSpinnerService } from 'ngx-spinner';
import { ToastrService } from 'ngx-toastr';
import { IawsService } from 'src/app/services/iaws.service';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit {
  @Output('admin_done') change_page: EventEmitter<string> = new EventEmitter<string>();
  @Input('hashtags') hashtags: any[] = [];

  initial_date: string = '';
  final_date: string = '';

  constructor(
    private iaService: IawsService,
    private toastr: ToastrService,
    private spinner: NgxSpinnerService) { }

  ngOnInit(): void {
    const today = new Date();
    const year = today.getFullYear().toString();
    const month = (today.getMonth() + 1).toString().padStart(2, '0');
    const day = today.getDate().toString().padStart(2, '0');
    this.initial_date = `${year}-${month}-${(Number.parseInt(day) - 1).toString()}`;
    this.final_date = `${year}-${month}-${day}`;
  }

  buscar_tweets() {
    let hashtag_list: any[] = [];
    this.hashtags.forEach(element => {
      hashtag_list.push(element.text);
    });
    this.spinner.show();
    this.iaService.search_tweets_and_store_on_db(hashtag_list, this.initial_date, this.final_date).then((r: any) => {
      this.spinner.hide();
      if (r.status == 200) {
        this.toastr.success('Tweets Cargados Satisfactoriamente', 'Obtener Tweets por Hashtags');
      } else {
        this.toastr.error(r.response, 'Obtener Tweets por Hashtags');
      }
    }).catch(e => {
      console.log(e);
      this.toastr.error('Ocurrio un error', 'Obtener Tweets por Hashtags');
    })
  }
}

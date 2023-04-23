import { TestBed } from '@angular/core/testing';

import { IawsService } from './iaws.service';

describe('IawsService', () => {
  let service: IawsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(IawsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
